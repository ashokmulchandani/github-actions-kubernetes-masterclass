CLUSTER  ?= skillpulse
NAMESPACE ?= skillpulse
BACKEND_IMAGE  ?= trainwithshubham/skillpulse-backend:latest
FRONTEND_IMAGE ?= trainwithshubham/skillpulse-frontend:latest

.PHONY: up down build load apply status logs mysql restart

up: ## One-shot: build images, create cluster, load images, apply manifests
	$(MAKE) build
	kind create cluster --config k8s/kind-config.yaml --name $(CLUSTER)
	$(MAKE) load
	$(MAKE) apply
	@echo
	@echo "  SkillPulse is live at http://localhost:8888"
	@echo

build: ## Build backend + frontend images for the host's architecture
	docker build -t $(BACKEND_IMAGE)  ./backend
	docker build -t $(FRONTEND_IMAGE) ./frontend

load: ## Push built images into the kind node
	kind load docker-image $(BACKEND_IMAGE)  --name $(CLUSTER)
	kind load docker-image $(FRONTEND_IMAGE) --name $(CLUSTER)

apply: ## Apply manifests and wait for rollouts
	kubectl apply -f k8s/00-namespace.yaml \
	              -f k8s/10-mysql.yaml \
	              -f k8s/20-backend.yaml \
	              -f k8s/30-frontend.yaml
	kubectl rollout status statefulset/mysql    -n $(NAMESPACE) --timeout=180s
	kubectl rollout status deployment/backend   -n $(NAMESPACE) --timeout=120s
	kubectl rollout status deployment/frontend  -n $(NAMESPACE) --timeout=60s

down: ## Delete the cluster
	kind delete cluster --name $(CLUSTER)

status: ## Quick health snapshot
	@kubectl get pods,svc,endpoints -n $(NAMESPACE)

logs: ## Tail all three workloads at once
	@kubectl logs -n $(NAMESPACE) -l 'app in (mysql,backend,frontend)' --all-containers --tail=50 -f --max-log-requests=10

mysql: ## Open a mysql shell into the StatefulSet pod
	kubectl exec -it -n $(NAMESPACE) mysql-0 -- mysql -uskillpulse -pskillpulse123 skillpulse


restart: ## Rebuild + reload images, roll backend + frontend
	$(MAKE) build
	$(MAKE) load
	kubectl rollout restart deployment/backend deployment/frontend -n $(NAMESPACE)
	kubectl rollout status  deployment/backend  -n $(NAMESPACE) --timeout=120s
	kubectl rollout status  deployment/frontend -n $(NAMESPACE) --timeout=60s

setup: ## Install Docker, Kind, kubectl on fresh EC2
	bash scripts/setup-all.sh
backup: ## Backup MySQL database locally
	bash scripts/backup-db.sh

backup-s3: ## Backup MySQL database to S3
	bash scripts/backup-to-s3.sh

backup-cron: ## Setup daily automatic backup cron job
	bash scripts/setup-cron-backup.sh

restore: ## Restore database from backup file (usage: make restore FILE=backups/file.sql)
	bash scripts/restore-db.sh $(FILE)

deploy-dev: ## Deploy app to dev environment
	kubectl create namespace skillpulse-dev --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f k8s/configmap-dev.yaml
	kubectl apply -f k8s/10-mysql.yaml -f k8s/20-backend.yaml -f k8s/30-frontend.yaml -n skillpulse-dev

deploy-stg: ## Deploy app to staging environment
	kubectl create namespace skillpulse-stg --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f k8s/configmap-stg.yaml
	kubectl apply -f k8s/10-mysql.yaml -f k8s/20-backend.yaml -f k8s/30-frontend.yaml -n skillpulse-stg

deploy-prd: ## Deploy app to production environment
	kubectl create namespace skillpulse-prd --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f k8s/configmap-prd.yaml
	kubectl apply -f k8s/10-mysql.yaml -f k8s/20-backend.yaml -f k8s/30-frontend.yaml -n skillpulse-prd


build-optimized: ## Build optimized (smaller) backend image
	docker build -t skillpulse-backend-optimized -f backend/Dockerfile.optimized ./backend
	docker build -t $(FRONTEND_IMAGE) ./frontend

size: ## Compare Docker image sizes
	@echo "=== Docker Image Sizes ==="
	@docker images | grep skillpulse

	
scan: ## Scan Docker images for vulnerabilities
	bash scripts/scan-images.sh

install-trivy: ## Install Trivy security scanner
	bash scripts/install-trivy.sh

mysql: ## Open a mysql shell into the StatefulSet pod
	kubectl exec -it -n $(NAMESPACE) mysql-0 -- mysql -uskillpulse -pskillpulse123 skillpulse

sonarqube: ## Start SonarQube locally for code scanning
	bash scripts/install-sonarqube.sh

lint: ## Run code quality checks on backend
	cd backend && go vet ./...
	cd backend && staticcheck ./...

lint-frontend: ## Check frontend HTML (optional)
	@echo "Frontend is static HTML/CSS/JS - no linting needed"



monitoring: ## Install Prometheus + Grafana + Loki in cluster
	kubectl apply -f k8s/monitoring/prometheus.yaml
	kubectl apply -f k8s/monitoring/alert-rules.yaml
	kubectl apply -f k8s/monitoring/grafana.yaml
	kubectl apply -f k8s/monitoring/loki.yaml
	@echo ""
	@echo "  Prometheus: http://localhost:30090"
	@echo "  Grafana:    http://localhost:30030 (admin/admin123)"
	@echo "  Loki:       Connected to Grafana"
	@echo ""

monitoring-down: ## Remove Prometheus + Grafana
	kubectl delete -f k8s/monitoring/grafana.yaml --ignore-not-found
	kubectl delete -f k8s/monitoring/prometheus.yaml --ignore-not-found
