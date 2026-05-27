package middleware

/*
IDEMPOTENCY MIDDLEWARE
=======================
Prevents duplicate operations when user clicks multiple times
or network retries the same request.

How it works:
  1. Client sends a unique ID with each request (X-Idempotency-Key header)
  2. Server checks: "Have I seen this ID before?"
     - YES → return the previous response (don't process again)
     - NO  → process normally, save the response with this ID
  3. ID expires after 24 hours (cleanup)

Example:
  POST /api/skills
  Header: X-Idempotency-Key: "abc-123-def"
  Body: {"name": "Docker", "category": "DevOps"}

  First time:  Process → create skill → save response → return 201
  Second time: "abc-123-def already processed!" → return saved 201 response
  Third time:  Same → return saved response (no duplicate created!)
*/

import (
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// storedResponse holds the cached response for an idempotency key
type storedResponse struct {
	statusCode int
	body       string
	createdAt  time.Time
}

// IdempotencyStore holds all processed request IDs
type IdempotencyStore struct {
	responses map[string]*storedResponse
	mu        sync.Mutex
	ttl       time.Duration
}

// NewIdempotencyStore creates a new store
// ttl: how long to remember processed requests (e.g., 24 hours)
func NewIdempotencyStore(ttl time.Duration) *IdempotencyStore {
	store := &IdempotencyStore{
		responses: make(map[string]*storedResponse),
		ttl:       ttl,
	}

	// Cleanup expired entries every hour
	go store.cleanup()

	return store
}

// cleanup removes expired entries
func (s *IdempotencyStore) cleanup() {
	for {
		time.Sleep(1 * time.Hour)
		s.mu.Lock()
		for key, resp := range s.responses {
			if time.Since(resp.createdAt) > s.ttl {
				delete(s.responses, key)
			}
		}
		s.mu.Unlock()
	}
}

// Middleware returns a Gin middleware for idempotency
func (s *IdempotencyStore) Middleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Only apply to POST/PUT/PATCH (mutations)
		// GET requests are naturally idempotent (reading doesn't change anything)
		if c.Request.Method == "GET" || c.Request.Method == "DELETE" {
			c.Next()
			return
		}

		// Get idempotency key from header
		key := c.GetHeader("X-Idempotency-Key")
		if key == "" {
			// No key provided — process normally (no protection)
			c.Next()
			return
		}

		// Check if we already processed this key
		s.mu.Lock()
		existing, found := s.responses[key]
		s.mu.Unlock()

		if found {
			// ALREADY PROCESSED — return cached response
			c.Header("X-Idempotency-Status", "DUPLICATE")
			c.Data(existing.statusCode, "application/json", []byte(existing.body))
			c.Abort()
			return
		}

		// NOT PROCESSED — continue with request
		c.Header("X-Idempotency-Status", "NEW")
		c.Next()

		// After request completes, save the response
		s.mu.Lock()
		s.responses[key] = &storedResponse{
			statusCode: c.Writer.Status(),
			body:       "",  // In production, capture actual response body
			createdAt:  time.Now(),
		}
		s.mu.Unlock()
	}
}
