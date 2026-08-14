"""
Configuration constants for the Ollama MCP Server.
Model routing, file extension mappings, and RAG pipeline settings.
"""

# ---------------------------------------------------------------------------
# Model routing — maps task context types to the best local model
# ---------------------------------------------------------------------------

MODEL_ROUTES: dict[str, str] = {
    "code": "qwen2.5:1.5b-ctx",
    "reasoning": "qwen2.5:1.5b-ctx",
    "general": "qwen2.5:1.5b",
    "fast": "qwen2.5:1.5b",
    "summarize": "qwen2.5:1.5b-ctx",
    "embed": "nomic-embed-text:latest",
    "lightweight": "qwen2.5:1.5b",
}

DEFAULT_MODEL = "qwen2.5:1.5b-ctx"

# Capabilities metadata for ollama_list_models
MODEL_CAPABILITIES: dict[str, str] = {
    "qwen2.5:1.5b": "General chat, extraction (small, CPU-friendly)",
    "qwen2.5:1.5b-ctx": "General chat with 8192 context window",
    "nomic-embed-text:latest": "Embeddings for RAG (768-dim)",
}

# ---------------------------------------------------------------------------
# RAG pipeline constants
# ---------------------------------------------------------------------------

INDEXABLE_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c_header",
    ".hpp": "cpp_header",
    ".hxx": "cpp_header",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".lua": "lua",
    ".sh": "shell",
    ".bash": "shell",
    ".md": "markdown",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".cfg": "config",
    ".ini": "config",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".pdf": "pdf",
    ".r": "r",
    ".R": "r",
    ".swift": "swift",
    ".kt": "kotlin",
    ".cs": "csharp",
    ".php": "php",
    ".pl": "perl",
    ".zig": "zig",
    ".asm": "assembly",
    ".s": "assembly",
    ".S": "assembly",
    ".cmake": "cmake",
    ".makefile": "make",
    ".mk": "make",
}

SKIP_DIRS: set[str] = {
    ".git", "__pycache__", "node_modules", "build", "dist", ".rag",
    ".venv", "venv", "env", ".env", ".tox", ".mypy_cache", ".pytest_cache",
    ".eggs", "*.egg-info", "target", "out", "bin", "obj", ".idea", ".vscode",
    ".vs", "Debug", "Release", "x64", "x86", ".cache",
}

MAX_FILE_SIZE = 512 * 1024              # 512 KB for text/code files
MAX_PDF_FILE_SIZE = 50 * 1024 * 1024    # 50 MB for PDFs
EMBED_BATCH_SIZE = 20
RAG_COLLECTION_NAME = "rag_chunks"
