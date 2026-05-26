package handlers

/*
CACHE PATTERN REFERENCE
=======================
This file shows how to add Redis caching to the existing handlers.
To enable: replace GetSkills in main.go with GetSkillsCached.

Flow:
  1. Request comes in
  2. Check Redis → found? Return immediately (CACHE HIT)
  3. Not found? → Query MySQL → Save to Redis → Return (CACHE MISS)
  4. When data changes (Create/Delete) → Clear the cache

This reduces MySQL load by ~90% for read-heavy endpoints.
*/

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/trainwithshubham/skillpulse/cache"
	"github.com/trainwithshubham/skillpulse/database"
	"github.com/trainwithshubham/skillpulse/models"
)

const skillsCacheKey = "skills:all"

// GetSkillsCached - same as GetSkills but with Redis cache
func GetSkillsCached(c *gin.Context) {
	// Step 1: Check Redis cache first
	cached, found := cache.Get(skillsCacheKey)
	if found {
		log.Println("⚡ CACHE HIT: skills:all")
		c.Header("X-Cache", "HIT")
		c.Data(http.StatusOK, "application/json", []byte(cached))
		return
	}

	// Step 2: Cache MISS - query MySQL
	log.Println("💾 CACHE MISS: skills:all → querying MySQL")
	rows, err := database.DB.Query(`
		SELECT s.id, s.name, s.category, s.target_hours,
		       COALESCE(SUM(l.hours), 0) as total_hours, s.created_at
		FROM skills s
		LEFT JOIN learning_logs l ON s.id = l.skill_id
		GROUP BY s.id, s.name, s.category, s.target_hours, s.created_at
		ORDER BY s.created_at DESC
	`)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	skills := []models.Skill{}
	for rows.Next() {
		var s models.Skill
		if err := rows.Scan(&s.ID, &s.Name, &s.Category, &s.TargetHours, &s.TotalHours, &s.CreatedAt); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		skills = append(skills, s)
	}

	// Step 3: Save to Redis cache (expires in 5 minutes)
	jsonData, _ := json.Marshal(skills)
	cache.Set(skillsCacheKey, string(jsonData), cache.DefaultTTL)

	c.Header("X-Cache", "MISS")
	c.JSON(http.StatusOK, skills)
}

// CreateSkillCached - creates skill and clears cache
func CreateSkillCached(c *gin.Context) {
	var req models.CreateSkillRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	result, err := database.DB.Exec(
		"INSERT INTO skills (name, category, target_hours) VALUES (?, ?, ?)",
		req.Name, req.Category, req.TargetHours,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Clear cache because data changed
	cache.Delete(skillsCacheKey)
	log.Println("🗑️ Cache cleared: skills:all (new skill created)")

	id, _ := result.LastInsertId()
	c.JSON(http.StatusCreated, gin.H{"id": id, "message": "Skill created"})
}

// DeleteSkillCached - deletes skill and clears cache
func DeleteSkillCached(c *gin.Context) {
	id := c.Param("id")

	result, err := database.DB.Exec("DELETE FROM skills WHERE id = ?", id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	rows, _ := result.RowsAffected()
	if rows == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Skill not found"})
		return
	}

	// Clear cache because data changed
	cache.Delete(skillsCacheKey)
	log.Println("🗑️ Cache cleared: skills:all (skill deleted)")

	c.JSON(http.StatusOK, gin.H{"message": "Skill deleted"})
}
