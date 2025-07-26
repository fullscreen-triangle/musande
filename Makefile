# Makefile for Musande S-Entropy Framework
# The Mathematical Substrate of Consciousness and Universal Problem Solving

.PHONY: all build test check clean doc install bench profile setup-dev help
.DEFAULT_GOAL := help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
MAGENTA := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Project information
PROJECT_NAME := musande
VERSION := $(shell grep '^version' Cargo.toml | sed 's/.*"\(.*\)".*/\1/')
RUST_VERSION := $(shell rustc --version | cut -d' ' -f2)

# Build configurations
CARGO_FLAGS := --workspace --all-features
RELEASE_FLAGS := --release
TEST_FLAGS := --workspace --all-features
DOC_FLAGS := --workspace --all-features --open

# S-Entropy specific targets
S_ENTROPY_CORES := musande-core musande-alignment musande-navigation musande-ridiculous
BMD_SERVICES := musande-service musande-cli
BINDINGS := musande-bindings/python musande-bindings/javascript musande-bindings/c

## 🧠 Primary Targets

all: check test build doc ## Build everything (check, test, build, doc)
	@echo "$(GREEN)✅ All Musande S-Entropy Framework components built successfully$(NC)"

build: ## 🔨 Build all crates in the workspace
	@echo "$(BLUE)🔨 Building Musande S-Entropy Framework...$(NC)"
	cargo build $(CARGO_FLAGS)
	@echo "$(GREEN)✅ Build complete$(NC)"

build-release: ## 🚀 Build optimized release version
	@echo "$(BLUE)🚀 Building release version of Musande...$(NC)"
	cargo build $(CARGO_FLAGS) $(RELEASE_FLAGS)
	@echo "$(GREEN)✅ Release build complete$(NC)"

## 🧪 Testing and Quality

test: ## 🧪 Run all tests with S-entropy validation
	@echo "$(BLUE)🧪 Testing BMD and S-entropy algorithms...$(NC)"
	cargo test $(TEST_FLAGS)
	@echo "$(GREEN)✅ All tests passed$(NC)"

test-consciousness: ## 🧠 Run consciousness-specific tests
	@echo "$(BLUE)🧠 Testing consciousness algorithms...$(NC)"
	cargo test -p musande-core --features consciousness-tests
	@echo "$(GREEN)✅ Consciousness tests passed$(NC)"

test-bmd: ## 🔬 Run Biological Maxwell Demon tests
	@echo "$(BLUE)🔬 Testing BMD operations...$(NC)"
	cargo test -p musande-core --features bmd-tests
	@echo "$(GREEN)✅ BMD tests passed$(NC)"

check: ## 🔍 Run clippy and format checks
	@echo "$(BLUE)🔍 Checking code quality for consciousness-critical algorithms...$(NC)"
	cargo clippy $(CARGO_FLAGS) -- -D warnings
	cargo fmt --all -- --check
	@echo "$(GREEN)✅ Code quality checks passed$(NC)"

fix: ## 🔧 Auto-fix formatting and linting issues
	@echo "$(BLUE)🔧 Auto-fixing code issues...$(NC)"
	cargo fmt --all
	cargo clippy $(CARGO_FLAGS) --fix --allow-dirty --allow-staged
	@echo "$(GREEN)✅ Code fixes applied$(NC)"

## 📊 Performance and Benchmarking

bench: ## 📊 Run S-entropy performance benchmarks
	@echo "$(BLUE)📊 Benchmarking S-entropy navigation performance...$(NC)"
	cargo bench --workspace
	@echo "$(GREEN)✅ Benchmarks complete$(NC)"

bench-consciousness: ## 🧠 Benchmark consciousness algorithms specifically
	@echo "$(BLUE)🧠 Benchmarking consciousness performance...$(NC)"
	cargo bench -p musande-core --features bench-consciousness
	@echo "$(GREEN)✅ Consciousness benchmarks complete$(NC)"

profile: ## 🎯 Profile S-entropy algorithms with flamegraph
	@echo "$(BLUE)🎯 Profiling S-entropy navigation...$(NC)"
	cargo flamegraph --bench s_entropy_navigation
	@echo "$(GREEN)✅ Profiling complete, see flamegraph.svg$(NC)"

## 📚 Documentation

doc: ## 📚 Generate and open documentation
	@echo "$(BLUE)📚 Generating S-Entropy Framework documentation...$(NC)"
	cargo doc $(DOC_FLAGS)
	@echo "$(GREEN)✅ Documentation generated$(NC)"

doc-private: ## 📖 Generate documentation including private items
	@echo "$(BLUE)📖 Generating complete documentation...$(NC)"
	cargo doc $(DOC_FLAGS) --document-private-items
	@echo "$(GREEN)✅ Complete documentation generated$(NC)"

## 🔧 Development Setup

setup-dev: ## 🔧 Set up development environment
	@echo "$(BLUE)🔧 Setting up Musande development environment...$(NC)"
	rustup component add rustfmt clippy
	rustup target add wasm32-unknown-unknown
	@if command -v python3 >/dev/null 2>&1; then \
		echo "$(YELLOW)Setting up Python bindings environment...$(NC)"; \
		python3 -m venv venv; \
		./venv/bin/pip install maturin pytest numpy; \
	fi
	@if command -v node >/dev/null 2>&1; then \
		echo "$(YELLOW)Setting up JavaScript bindings environment...$(NC)"; \
		npm install -g @napi-rs/cli; \
	fi
	@echo "$(GREEN)✅ Development environment ready$(NC)"

install-tools: ## 🛠️ Install additional development tools
	@echo "$(BLUE)🛠️ Installing development tools...$(NC)"
	cargo install cargo-watch cargo-expand cargo-audit cargo-udeps
	cargo install flamegraph cargo-benchcmp criterion-table
	@echo "$(GREEN)✅ Development tools installed$(NC)"

## 🐍 Language Bindings

build-python: ## 🐍 Build Python bindings
	@echo "$(BLUE)🐍 Building Python bindings for S-Entropy...$(NC)"
	cd crates/musande-bindings/python && maturin develop --features python-bindings
	@echo "$(GREEN)✅ Python bindings built$(NC)"

build-js: ## 🟨 Build JavaScript bindings
	@echo "$(BLUE)🟨 Building JavaScript bindings...$(NC)"
	cd crates/musande-bindings/javascript && napi build --platform
	@echo "$(GREEN)✅ JavaScript bindings built$(NC)"

build-c: ## ⚡ Build C bindings
	@echo "$(BLUE)⚡ Building C bindings...$(NC)"
	cd crates/musande-bindings/c && cargo build --release
	cbindgen --config cbindgen.toml --crate musande-bindings-c --output musande.h
	@echo "$(GREEN)✅ C bindings built$(NC)"

test-bindings: build-python build-js ## 🧪 Test all language bindings
	@echo "$(BLUE)🧪 Testing language bindings...$(NC)"
	cd crates/musande-bindings/python && python -m pytest
	cd crates/musande-bindings/javascript && npm test
	@echo "$(GREEN)✅ All bindings tested$(NC)"

## 🐳 Deployment and Distribution

build-docker: ## 🐳 Build Docker image
	@echo "$(BLUE)🐳 Building Musande Docker image...$(NC)"
	docker build -t musande:$(VERSION) -f docker/Dockerfile .
	@echo "$(GREEN)✅ Docker image built: musande:$(VERSION)$(NC)"

deploy-local: build-release ## 🚀 Deploy services locally
	@echo "$(BLUE)🚀 Deploying Musande services locally...$(NC)"
	docker-compose -f docker/docker-compose.local.yml up -d
	@echo "$(GREEN)✅ Local deployment complete$(NC)"

## 📦 Package Management

publish-dry: ## 📦 Dry run package publishing
	@echo "$(BLUE)📦 Dry run publishing S-Entropy packages...$(NC)"
	for crate in $(S_ENTROPY_CORES); do \
		echo "$(YELLOW)Dry run: $$crate$(NC)"; \
		cargo publish -p $$crate --dry-run; \
	done
	@echo "$(GREEN)✅ Dry run complete$(NC)"

install: build-release ## 📥 Install Musande CLI locally
	@echo "$(BLUE)📥 Installing Musande CLI...$(NC)"
	cargo install --path crates/musande-cli --force
	@echo "$(GREEN)✅ Musande CLI installed$(NC)"

## 🧹 Cleanup

clean: ## 🧹 Clean build artifacts
	@echo "$(BLUE)🧹 Cleaning build artifacts...$(NC)"
	cargo clean
	@if [ -d "venv" ]; then rm -rf venv; fi
	@if [ -d "node_modules" ]; then rm -rf node_modules; fi
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

clean-docs: ## 📚 Clean documentation
	@echo "$(BLUE)📚 Cleaning documentation...$(NC)"
	cargo clean --doc
	@echo "$(GREEN)✅ Documentation cleaned$(NC)"

## 🔍 Analysis and Debugging

audit: ## 🔍 Security audit
	@echo "$(BLUE)🔍 Running security audit...$(NC)"
	cargo audit
	@echo "$(GREEN)✅ Security audit complete$(NC)"

deps: ## 📋 Show dependency tree
	@echo "$(BLUE)📋 Dependency tree:$(NC)"
	cargo tree

udeps: ## 🕵️ Find unused dependencies
	@echo "$(BLUE)🕵️ Finding unused dependencies...$(NC)"
	cargo +nightly udeps --all-targets --all-features

expand: ## 🔬 Expand macros (requires cargo-expand)
	@echo "$(BLUE)🔬 Expanding macros...$(NC)"
	cargo expand --lib -p musande-core

## 🎯 S-Entropy Specific Targets

s-entropy-demo: ## 🎯 Run S-entropy navigation demo
	@echo "$(BLUE)🎯 Running S-entropy navigation demonstration...$(NC)"
	cargo run --example s_entropy_demo --features demo
	@echo "$(GREEN)✅ S-entropy demo complete$(NC)"

bmd-demo: ## 🔬 Run BMD operation demonstration
	@echo "$(BLUE)🔬 Running BMD operation demonstration...$(NC)"
	cargo run --example bmd_demo --features demo
	@echo "$(GREEN)✅ BMD demo complete$(NC)"

consciousness-demo: ## 🧠 Run consciousness framework demonstration
	@echo "$(BLUE)🧠 Running consciousness framework demonstration...$(NC)"
	cargo run --example consciousness_demo --features demo
	@echo "$(GREEN)✅ Consciousness demo complete$(NC)"

## 📊 Reporting

coverage: ## 📊 Generate test coverage report
	@echo "$(BLUE)📊 Generating test coverage...$(NC)"
	cargo tarpaulin --out Html --output-dir coverage
	@echo "$(GREEN)✅ Coverage report generated in coverage/$(NC)"

size-report: build-release ## 📏 Generate binary size report
	@echo "$(BLUE)📏 Binary size analysis:$(NC)"
	@echo "$(CYAN)musande-cli: $$(du -h target/release/musande-cli | cut -f1)$(NC)"
	@echo "$(CYAN)musande-service: $$(du -h target/release/musande-service | cut -f1)$(NC)"

## ℹ️ Information

version: ## ℹ️ Show version information
	@echo "$(CYAN)Musande S-Entropy Framework v$(VERSION)$(NC)"
	@echo "$(CYAN)Rust: $(RUST_VERSION)$(NC)"
	@echo "$(CYAN)Built for consciousness research and universal problem solving$(NC)"

status: ## 📊 Show project status
	@echo "$(CYAN)=== Musande S-Entropy Framework Status ===$(NC)"
	@echo "$(YELLOW)Version:$(NC) $(VERSION)"
	@echo "$(YELLOW)Rust Version:$(NC) $(RUST_VERSION)"
	@echo "$(YELLOW)Core Crates:$(NC) $(words $(S_ENTROPY_CORES))"
	@echo "$(YELLOW)Services:$(NC) $(words $(BMD_SERVICES))"
	@echo "$(YELLOW)Language Bindings:$(NC) $(words $(BINDINGS))"
	@if [ -f "target/release/musande-cli" ]; then \
		echo "$(GREEN)✅ Release build ready$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ Release build needed$(NC)"; \
	fi

help: ## ❓ Show this help message
	@echo "$(CYAN)=== Musande S-Entropy Framework Build System ===$(NC)"
	@echo "$(CYAN)The Mathematical Substrate of Consciousness and Universal Problem Solving$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage: make <target>$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "$(BLUE)Available targets:$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 4) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(CYAN)For the complete S-Entropy Framework documentation, run: make doc$(NC)" 