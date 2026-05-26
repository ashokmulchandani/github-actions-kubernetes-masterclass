package cache

import (
	"context"
	"log"
	"os"
	"time"

	"github.com/redis/go-redis/v9"
)

var Client *redis.Client
var Ctx = context.Background()

// Default TTL for cached data (5 minutes)
const DefaultTTL = 5 * time.Minute

func Connect() {
	redisHost := os.Getenv("REDIS_HOST")
	if redisHost == "" {
		redisHost = "redis"
	}
	redisPort := os.Getenv("REDIS_PORT")
	if redisPort == "" {
		redisPort = "6379"
	}

	Client = redis.NewClient(&redis.Options{
		Addr: redisHost + ":" + redisPort,
		DB:   0,
	})

	// Test connection
	_, err := Client.Ping(Ctx).Result()
	if err != nil {
		log.Printf("⚠️ Redis not available: %v (caching disabled)", err)
		Client = nil
		return
	}

	log.Printf("✅ Connected to Redis at %s:%s", redisHost, redisPort)
}

// Get retrieves a value from cache. Returns "" if not found.
func Get(key string) (string, bool) {
	if Client == nil {
		return "", false
	}

	val, err := Client.Get(Ctx, key).Result()
	if err == redis.Nil {
		return "", false // Key doesn't exist
	}
	if err != nil {
		return "", false // Redis error
	}

	return val, true // Cache HIT
}

// Set stores a value in cache with TTL
func Set(key string, value string, ttl time.Duration) {
	if Client == nil {
		return
	}

	Client.Set(Ctx, key, value, ttl)
}

// Delete removes a key from cache (used when data changes)
func Delete(key string) {
	if Client == nil {
		return
	}

	Client.Del(Ctx, key)
}

// DeletePattern removes all keys matching a pattern (e.g., "skills:*")
func DeletePattern(pattern string) {
	if Client == nil {
		return
	}

	keys, _ := Client.Keys(Ctx, pattern).Result()
	if len(keys) > 0 {
		Client.Del(Ctx, keys...)
	}
}
