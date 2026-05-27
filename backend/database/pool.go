package database

/*
CONNECTION POOLING
==================
Instead of opening a new database connection for every request,
we keep a POOL of connections ready to use.

Think of it like:
  Without pool: Build a bridge every time you cross the river. Demolish after.
  With pool:    Build 10 bridges once. Everyone uses them. Never demolish.

Settings explained:
  MaxOpenConns(20):     Maximum 20 connections open at same time
  MaxIdleConns(10):     Keep 10 connections ready even when not busy
  ConnMaxLifetime(5m):  Replace a connection after 5 minutes (keeps them fresh)
  ConnMaxIdleTime(1m):  Close idle connections after 1 minute (save resources)

Why these numbers?
  - 20 max open: enough for our traffic, won't overwhelm MySQL
  - 10 idle: ready for sudden traffic spike (no cold start)
  - 5 min lifetime: prevents stale connections (MySQL might drop old ones)
  - 1 min idle time: frees resources when traffic is low
*/

import (
	"time"
)

// ConfigurePool sets up connection pooling for the database
// Call this after database.Connect()
func ConfigurePool() {
	if DB == nil {
		return
	}

	// Max connections open at the same time
	// Too low: requests queue up waiting for a connection
	// Too high: MySQL gets overwhelmed
	DB.SetMaxOpenConns(20)

	// Connections kept ready (idle) for instant use
	// These are "warm" — no delay when request comes in
	DB.SetMaxIdleConns(10)

	// Replace connections after 5 minutes
	// Prevents "stale connection" errors
	DB.SetConnMaxLifetime(5 * time.Minute)

	// Close idle connections after 1 minute
	// Saves resources when traffic is low
	DB.SetConnMaxIdleTime(1 * time.Minute)
}

/*
HOW TO USE:

In main.go:
  database.Connect()
  database.ConfigurePool()  // Add this line!

That's it. One line. Go's database/sql handles the rest automatically.

What happens behind the scenes:
  Request 1: "I need a connection" → Pool: "Here, take this one" (instant)
  Request 1: "Done with query" → Pool: "I'll keep it warm for next person"
  Request 2: "I need a connection" → Pool: "Here, same one" (instant, reused!)

  vs without pool:
  Request 1: "I need a connection" → MySQL: "OK let me create one..." (50ms)
  Request 1: "Done" → Connection destroyed
  Request 2: "I need a connection" → MySQL: "OK creating again..." (50ms)
*/
