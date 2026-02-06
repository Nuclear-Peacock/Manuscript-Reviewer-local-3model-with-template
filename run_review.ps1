param(
  [Parameter(Mandatory=$true)]
  [string]$InputPdf,

  [string]$OutFile = "outputs\review.md",

  [ValidateSet("original_research","education","ai","systematic_review","other")]
  [string]$ManuscriptType = "original_research",

  [ValidateSet("diagnostic_accuracy","prediction_model","interventional","educational_intervention","systematic_review","other")]
  [string]$StudyDesign = "diagnostic_accuracy",

  [switch]$HasAI,

  [string[]]$FigureImages = @(),

  [string]$CriticModel = "deepseek-r1:70b",
  [string]$WriterModel = "llama3.3:70b",
  [string]$VlmModel = "qwen2.5vl:7b",

  [int]$NumCtx = 16384,
  [double]$Temperature = 0.2
)

# Always run from repo root
Set-Location $PSScriptRoot

# Activate venv
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
  . .\.venv\Scripts\Activate.ps1
} else {
  Write-Error "Virtual environment not found. Run: python -m venv .venv"
  exit 1
}

# Ensure outputs folder
if (!(Test-Path ".\outputs")) { New-Item -ItemType Directory -Path ".\outputs" | Out-Null }

# Build base args
$args = @(
  "-m","reviewer.cli",
  "--input",$InputPdf,
  "--rubric","config\rubrics\core_rubric.json",
  "--out",$OutFile,
  "--manuscript_type",$ManuscriptType,
  "--study_design",$StudyDesign,
  "--critic_model",$CriticModel,
  "--writer_model",$WriterModel,
  "--vlm_model",$VlmModel,
  "--num_ctx",$NumCtx.ToString(),
  "--temperature",$Temperature.ToString()
)

if ($HasAI) { $args += "--has_ai" }

if ($FigureImages.Count -gt 0) {
  $args += "--figure_images"
  $args += $FigureImages
}

python @args
