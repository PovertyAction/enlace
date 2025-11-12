# %% [markdown]
# # Paper Summarization Example
#
# This example demonstrates using the summarization API to generate structured
# research summaries from academic papers using LLMs.
#
# **Note:** The summarization functionality is referenced in the API_GUIDE.md but
# the actual implementation may still be in development. This example shows the
# expected API usage based on the documentation.
#
# **Requirements:**
# - ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable set

# %%
import os
from pathlib import Path

# Note: These imports are based on API_GUIDE.md
# The actual module structure may differ
try:
    from enlace.core.config import SummaryConfig
    from enlace.core.summarizer import PaperSummarizer
except ImportError:
    print("Warning: Summarization modules not yet implemented")
    print("This example shows expected API usage from API_GUIDE.md")

# %% [markdown]
# ## Check API Keys

# %%
# Check for API keys
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

if anthropic_key:
    print("✓ Anthropic API key found")
elif openai_key:
    print("✓ OpenAI API key found")
else:
    print("Error: No API key found")
    print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")

# %% [markdown]
# ## Basic Summarization
#
# Generate a standard summary of a research paper.

# %%
paper_path = Path("paper.pdf")

# Note: API based on docs/API_GUIDE.md
# Actual implementation may differ
config = SummaryConfig(
    llm_provider="anthropic",  # or "openai"
    model="claude-3-5-sonnet-20241022",
    detail_level="standard",  # brief, standard, detailed
    output_format="json",  # json, markdown, text
)

summarizer = PaperSummarizer(config)

# Generate summary
print(f"Generating summary for {paper_path.name}...")
summary = summarizer.summarize(paper_path)

# %% [markdown]
# ## Display Summary Results

# %%
# Display summary
print("\n=== Paper Summary ===")
print(f"Title: {summary.metadata.title}")
print(f"Authors: {', '.join(summary.metadata.authors)}")
print(f"Year: {summary.metadata.year}")

print("\n=== Abstract ===")
print(summary.abstract)

print("\n=== Research Question ===")
print(summary.research_question)

print("\n=== Methods ===")
print(f"Study design: {summary.methods.study_design}")
print(f"Sample size: {summary.methods.sample_size}")
print(f"Data source: {summary.methods.data_source}")

print("\n=== Key Findings ===")
for i, finding in enumerate(summary.key_findings, 1):
    print(f"{i}. {finding}")

print("\n=== Results ===")
print(f"Main result: {summary.results.main_result}")
print(f"Effect size: {summary.results.effect_size}")
print(f"Statistical significance: {summary.results.significance}")

# %% [markdown]
# ## Save Summary

# %%
# Save to file
output_path = Path("output") / f"{paper_path.stem}_summary.json"
summary.save(output_path)
print(f"\n✓ Summary saved to {output_path}")

# %% [markdown]
# ## Detailed Summary
#
# Generate a more comprehensive summary with additional context.

# %%
config_detailed = SummaryConfig(
    llm_provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    detail_level="detailed",
    output_format="markdown",
    temperature=0.3,
    max_tokens=4000,
)

summarizer_detailed = PaperSummarizer(config_detailed)

# Generate detailed summary
print("Generating detailed summary...")
summary_detailed = summarizer_detailed.summarize(paper_path)

# Save as markdown
output_md = Path("output") / f"{paper_path.stem}_summary_detailed.md"
summary_detailed.save(output_md)
print(f"✓ Detailed summary saved to {output_md}")

# %% [markdown]
# ## Brief Summary
#
# Generate a concise summary for quick review.

# %%
config_brief = SummaryConfig(
    llm_provider="anthropic",
    detail_level="brief",
    output_format="text",
)

summarizer_brief = PaperSummarizer(config_brief)

# Generate brief summary
summary_brief = summarizer_brief.summarize(paper_path)

print("\n=== Brief Summary ===")
print(summary_brief.text)

# %% [markdown]
# ## Batch Summarization
#
# Generate summaries for multiple papers.

# %%
from enlace.core.batch import BatchProcessor  # noqa: E402

# Batch summarization
processor = BatchProcessor(
    output_dir=Path("batch_summaries"),
    workers=4,
    enable_summarization=True,  # Enable summarization
    summary_detail_level="standard",
)

# Process all papers
papers_dir = Path("papers")
print(f"Generating summaries for all papers in {papers_dir}...")
batch_summary = processor.process(papers_dir)

print(f"\n✓ Processed {batch_summary.papers_successful} papers")
print(f"Summaries saved to {processor.output_dir}")

# %% [markdown]
# ## Using OpenAI
#
# Generate summaries using OpenAI's models instead of Anthropic.

# %%
config_openai = SummaryConfig(
    llm_provider="openai",
    model="gpt-4",
    detail_level="standard",
    output_format="json",
)

summarizer_openai = PaperSummarizer(config_openai)

# Generate summary
summary_openai = summarizer_openai.summarize(paper_path)

print("\n=== OpenAI Summary ===")
print(f"Title: {summary_openai.metadata.title}")
print(f"Research question: {summary_openai.research_question}")

# %% [markdown]
# ## Custom Configuration from File
#
# Load configuration from a TOML file.

# %%
# Create a configuration file
config_file = Path("summary_config.toml")
config_file.write_text("""
[tool.enlace.summary]
llm_provider = "anthropic"
model = "claude-3-5-sonnet-20241022"
detail_level = "standard"
output_format = "json"
temperature = 0.3
max_tokens = 4000
""")

# Load from file
config_from_file = SummaryConfig.load_config(config_file=config_file)

summarizer_from_file = PaperSummarizer(config_from_file)
summary_from_file = summarizer_from_file.summarize(paper_path)

print(f"✓ Generated summary using configuration from {config_file}")

# %% [markdown]
# ## Environment Variable Configuration
#
# Configure summarization using environment variables.

# %%
# Set environment variables
os.environ["SUMMARY_LLM_PROVIDER"] = "anthropic"
os.environ["SUMMARY_DETAIL_LEVEL"] = "standard"
os.environ["SUMMARY_OUTPUT_FORMAT"] = "json"
os.environ["SUMMARY_TEMPERATURE"] = "0.3"
os.environ["SUMMARY_MAX_TOKENS"] = "4000"

# Load from environment
config_from_env = SummaryConfig.load_config()

summarizer_from_env = PaperSummarizer(config_from_env)
summary_from_env = summarizer_from_env.summarize(paper_path)

print("✓ Generated summary using environment variables")

# %% [markdown]
# ## Extract Specific Sections
#
# Extract and summarize specific sections of interest.

# %%
# Summarize with focus on specific aspects
config_methods = SummaryConfig(
    llm_provider="anthropic",
    detail_level="detailed",
    focus_sections=["methods", "results"],  # Focus on specific sections
)

summarizer_methods = PaperSummarizer(config_methods)
summary_methods = summarizer_methods.summarize(paper_path)

print("\n=== Methods Summary ===")
print(f"Study design: {summary_methods.methods.study_design}")
print(f"Estimation strategy: {summary_methods.methods.estimation_strategy}")
print(f"Sample: {summary_methods.methods.sample_description}")

print("\n=== Results Summary ===")
print(f"Main finding: {summary_methods.results.main_result}")
print(f"Treatment effect: {summary_methods.results.treatment_effect}")
print(f"Heterogeneity: {summary_methods.results.heterogeneity_analysis}")

# %% [markdown]
# ## Compare Summaries
#
# Compare summaries generated with different configurations.

# %%
# Generate summaries with different detail levels
levels = ["brief", "standard", "detailed"]
summaries = {}

for level in levels:
    config = SummaryConfig(
        llm_provider="anthropic",
        detail_level=level,
        output_format="json",
    )
    summarizer = PaperSummarizer(config)
    summaries[level] = summarizer.summarize(paper_path)

# Compare
print("\n=== Summary Comparison ===")
for level, summary in summaries.items():
    print(f"\n{level.upper()}:")
    print(f"  Token count: {summary.token_count}")
    print(f"  Processing time: {summary.processing_time_seconds:.1f}s")
    print(f"  Key findings: {len(summary.key_findings)}")
    print(f"  Length: {len(summary.text)} characters")
