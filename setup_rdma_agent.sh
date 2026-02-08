#!/bin/bash
# RDMA Agent System - Setup Script for Ubuntu 22.04

set -e

echo "=========================================="
echo "  RDMA Agent System Setup"
echo "=========================================="

# Create data directories
echo "[1/5] Creating data directories..."
sudo mkdir -p /var/lib/rdma_agent/chroma
sudo mkdir -p /var/log/rdma_agent
sudo chown -R $USER:$USER /var/lib/rdma_agent /var/log/rdma_agent

# Install Python dependencies
echo "[2/5] Installing Python dependencies..."
pip install -r rdma_agent_requirements.txt

# Copy env file if not exists
echo "[3/5] Setting up environment..."
if [ ! -f .env ]; then
    cp rdma_agent.env.example .env
    echo "  Created .env from template. Please edit it with your configuration."
else
    echo "  .env already exists, skipping."
fi

# Load sample knowledge base
echo "[4/5] Knowledge base documents ready at rdma_agent/knowledge_base/"
echo "  Upload these to Dify.ai or they will be auto-loaded into ChromaDB."

# Print status
echo "[5/5] Setup complete!"
echo ""
echo "=========================================="
echo "  Quick Start"
echo "=========================================="
echo ""
echo "1. Edit .env with your LLM/Embedding/Rerank API endpoints"
echo ""
echo "2. Start the agent:"
echo "   python -m uvicorn rdma_agent.app:app --host 0.0.0.0 --port 8900"
echo ""
echo "3. Open dashboard: http://localhost:8900"
echo "   API docs:       http://localhost:8900/docs"
echo ""
echo "4. To set up Dify.ai integration:"
echo "   - Import the workflow template from rdma_agent/dify/workflow.py"
echo "   - Create a dataset and upload knowledge_base/*.md files"
echo "   - Update DIFY_* settings in .env"
echo ""
echo "=========================================="
