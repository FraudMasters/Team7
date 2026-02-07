# Subtask 4-4: Neo4j Browser Graph Data Verification

## Overview

This document provides comprehensive instructions for verifying graph data in the Neo4j Browser UI after episode ingestion via the Graphiti API.

**Prerequisites:**
- Neo4j container running (http://localhost:7474)
- Backend service running with Graphiti integration
- At least one episode ingested via POST /api/v1/context/episodes

## Quick Start Verification

### Automated Script

Run the automated verification script:

```bash
./verify_neo4j_browser_data.sh
```

This script will:
- Check Neo4j container status
- Verify Neo4j Browser UI accessibility
- Query node and relationship counts (if cypher-shell is available)
- List node types/labels
- Provide manual verification instructions

### Manual Browser Verification

#### Step 1: Access Neo4j Browser

1. Open your web browser
2. Navigate to: **http://localhost:7474**
3. Login with credentials:
   - Username: `neo4j`
   - Password: Check your `NEO4J_PASSWORD` environment variable (default: `password`)

#### Step 2: Verify Graph Data

Run the following Cypher queries in the Neo4j Browser command bar:

**2.1. Count All Nodes**
```cypher
MATCH (n) RETURN count(n) AS total_nodes
```
**Expected:** After ingesting episodes, you should see a count > 0

**2.2. Count All Relationships**
```cypher
MATCH ()-[r]->() RETURN count(r) AS total_relationships
```
**Expected:** If entity extraction is complete, you should see relationships > 0

**2.3. List Node Labels/Types**
```cypher
CALL db.labels() YIELD label RETURN label
```
**Expected:** Common labels include:
- `Episode` (ingested episodes)
- `Entity` (extracted entities like people, organizations)
- `Relationship` (connections between entities)
- `Community` (entity clusters)

**2.4. View Recent Episodes**
```cypher
MATCH (n:Episode)
RETURN n.name, n.source, n.created_at
ORDER BY n.created_at DESC
LIMIT 10
```
**Expected:** List of recently ingested episodes with metadata

**2.5. Visualize Graph Sample**
```cypher
MATCH (n)
RETURN n
LIMIT 25
```
**Expected:** Visual graph display showing nodes and connections

**2.6. Check Graphiti Indices**
```cypher
SHOW INDEXES
```
**Expected:** Indices created by Graphiti for vector and text search

## Understanding the Graph Structure

### Graphiti Node Types

After episode ingestion, you should see the following node types:

#### Episode Nodes
- **Label:** `Episode`
- **Properties:**
  - `name`: Episode name/title
  - `body`: Episode content/text
  - `source`: Source identifier
  - `source_description`: Source description
  - `created_at`: Timestamp of ingestion
  - `episode_id`: Unique UUID

#### Entity Nodes
- **Label:** `Entity`
- **Properties:**
  - `name`: Entity name (e.g., "John Smith", "Python")
  - `entity_type`: Entity type (PERSON, ORGANIZATION, SKILL, etc.)
  - `description`: Entity description

#### Relationship Nodes
- **Label:** `Relationship`
- **Properties:**
  - `source`: Source entity
  - `target`: Target entity
  - `relationship_type`: Type of relationship
  - `description`: Relationship description

### Expected Graph After Ingestion

**Immediate (0-10 seconds):**
- Episode node appears (1 node)
- No entities or relationships yet

**After 10-30 seconds:**
- Episode node (1 node)
- Entity nodes (5-50+ depending on content)
- Relationship nodes (connecting entities)

**After 30+ seconds:**
- Full graph with entities, relationships, and possibly community nodes

## Troubleshooting

### Issue: Empty Graph (0 nodes)

**Symptoms:**
```cypher
MATCH (n) RETURN count(n)
// Returns: 0
```

**Possible Causes:**
1. No episodes have been ingested yet
2. GraphitiService is not initialized
3. Backend is not running

**Solutions:**
1. Ingest a test episode:
```bash
curl -X POST http://localhost:8000/api/v1/context/episodes \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Test Episode",
    "body": "John Smith is a Python developer with expertise in FastAPI and Docker.",
    "source": "verification",
    "source_description": "Manual verification test"
  }'
```

2. Check backend health:
```bash
curl http://localhost:8000/api/v1/context/health
```

3. Check GraphitiService initialization in backend logs:
```bash
docker-compose logs backend | grep -i graphiti
```

### Issue: Only Episode Nodes, No Entities

**Symptoms:**
```cypher
MATCH (n:Episode) RETURN count(n)
// Returns: 1

MATCH (n:Entity) RETURN count(n)
// Returns: 0
```

**Possible Causes:**
1. OpenAI API key is not configured
2. Entity extraction is still in progress
3. Graphiti telemetry/configuration issues

**Solutions:**
1. Verify OPENAI_API_KEY is set:
```bash
docker-compose exec backend env | grep OPENAI_API_KEY
```

2. Wait 30-60 seconds for entity extraction to complete

3. Check Graphiti configuration:
```bash
docker-compose exec backend env | grep GRAPHITI
```

4. Check backend logs for errors:
```bash
docker-compose logs backend | tail -50
```

### Issue: Cannot Login to Neo4j Browser

**Symptoms:**
- Login fails with "Authentication failed"
- Browser shows connection errors

**Possible Causes:**
1. Wrong password
2. Neo4j container not fully started
3. Port conflicts

**Solutions:**
1. Verify NEO4J_PASSWORD in .env:
```bash
grep NEO4J_PASSWORD .env
```

2. Check Neo4j container logs:
```bash
docker-compose logs neo4j | tail -30
```

3. Restart Neo4j container:
```bash
docker-compose restart neo4j
docker-compose logs -f neo4j
```

Wait for "Remote interface available" message before logging in.

### Issue: Neo4j Browser Not Accessible

**Symptoms:**
- Cannot access http://localhost:7474
- Connection refused or timeout

**Solutions:**
1. Verify Neo4j container is running:
```bash
docker ps | grep neo4j
```

2. Check if port 7474 is exposed:
```bash
netstat -an | grep 7474
# or
lsof -i :7474
```

3. Start Neo4j container:
```bash
docker-compose up -d neo4j
```

## Advanced Verification Queries

### Query Episode by ID
```cypher
MATCH (e:Episode {episode_id: 'your-episode-id'})
RETURN e
```

### Find All Entities for an Episode
```cypher
MATCH (e:Episode {episode_id: 'your-episode-id'})-[:HAS_ENTITY]->(entity:Entity)
RETURN entity.name, entity.entity_type
```

### Find Related Episodes
```cypher
MATCH (e1:Episode)-[:RELATED_TO]->(e2:Episode)
WHERE e1.episode_id = 'your-episode-id'
RETURN e2.name, e2.source
```

### Check Graph Density
```cypher
MATCH (n) OPTIONAL MATCH ()-[r]->()
RETURN count(DISTINCT n) AS nodes, count(r) AS relationships
```

### Find Most Connected Entities
```cypher
MATCH (e:Entity)
RETURN e.name, e.entity_type, size((e)-[:RELATED_TO]->()) AS connections
ORDER BY connections DESC
LIMIT 10
```

### View Graph Schema
```cypher
CALL db.schema.visualization()
```

## Verification Checklist

- [ ] Neo4j container is running (`docker ps | grep neo4j`)
- [ ] Neo4j Browser UI accessible at http://localhost:7474
- [ ] Can login with neo4j credentials
- [ ] Query `MATCH (n) RETURN count(n)` returns count > 0 after ingestion
- [ ] Episode nodes visible with correct metadata
- [ ] Entity nodes appear after 10-30 seconds (if OPENAI_API_KEY configured)
- [ ] Relationship nodes connect entities and episodes
- [ ] Graphiti indices exist (`SHOW INDEXES`)
- [ ] Can visualize graph with `MATCH (n) RETURN n LIMIT 25`

## Integration with Other Subtasks

This verification step (subtask-4-4) completes the integration and verification phase:

1. **subtask-4-1**: Neo4j container verified running
2. **subtask-4-2**: GraphitiService verified initialized
3. **subtask-4-3**: Episode ingestion and search flow verified
4. **subtask-4-4**: **Graph data visible in Neo4j Browser** ← YOU ARE HERE

After completing this verification, the full Graphiti integration is complete!

## Resources

- **Neo4j Browser Guide:** https://neo4j.com/docs/operations-manual/current/tools/neo4j-browser/
- **Cypher Query Language:** https://neo4j.com/docs/cypher-manual/
- **Graphiti Documentation:** https://github.com/getmesh/graphiti
- **Neo4j Docker Image:** https://hub.docker.com/_/neo4j

## Summary

Successfully verifying graph data in Neo4j Browser confirms:
- ✅ Neo4j is properly configured and accessible
- ✅ Episode ingestion is working via the API
- ✅ GraphitiService is extracting entities from episodes
- ✅ OpenAI API integration is functional (if entities extracted)
- ✅ Graph database is ready for semantic context search

This completes the integration and verification phase for the Graphiti-Core integration feature!
