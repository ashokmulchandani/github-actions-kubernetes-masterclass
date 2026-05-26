package database

/*
READ/WRITE SPLIT PATTERN
=========================
This file shows how to route database queries:
  - WRITES (INSERT, UPDATE, DELETE) → Primary (mysql)
  - READS (SELECT) → Replica (mysql-read)

To enable: use ReadDB for reads and DB (WriteDB) for writes.

Example:
  // Reading data (goes to replica - fast, doesn't block writes)
  database.ReadDB.Query("SELECT * FROM skills")

  // Writing data (goes to primary - the source of truth)
  database.DB.Exec("INSERT INTO skills ...")
*/

import (
	"database/sql"
	"fmt"
	"log"
	"os"
)

// ReadDB connects to the read replica (for SELECT queries)
var ReadDB *sql.DB

func ConnectReadReplica() {
	readHost := os.Getenv("DB_READ_HOST")
	if readHost == "" {
		// If no read replica configured, use primary for everything
		ReadDB = DB
		log.Println("ℹ️ No read replica configured. Using primary for reads.")
		return
	}

	port := os.Getenv("DB_PORT")
	user := os.Getenv("DB_USER")
	password := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")

	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true",
		user, password, readHost, port, dbName)

	var err error
	ReadDB, err = sql.Open("mysql", dsn)
	if err != nil {
		log.Printf("⚠️ Read replica connection failed: %v (falling back to primary)", err)
		ReadDB = DB
		return
	}

	// Connection pool settings for read replica
	ReadDB.SetMaxOpenConns(20)
	ReadDB.SetMaxIdleConns(10)

	if err = ReadDB.Ping(); err != nil {
		log.Printf("⚠️ Read replica ping failed: %v (falling back to primary)", err)
		ReadDB = DB
		return
	}

	log.Printf("✅ Connected to read replica at %s:%s", readHost, port)
}
