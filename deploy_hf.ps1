# Hugging Face Deployment Script
# Run this after creating a HuggingFace Space

$HF_REPO = Read-Host "Enter your HuggingFace Space URL (e.g., https://huggingface.co/spaces/YOUR_USERNAME/ai-business-analyst)"

if (-not $HF_REPO) {
    Write-Host "Error: HuggingFace Space URL is required"
    exit 1
}

# Convert Space URL to git URL
$HF_GIT_URL = $HF_REPO -replace "spaces/", "" -replace "huggingface.co/", "huggingface.co/spaces/"
$HF_GIT_URL = "https://huggingface.co/spaces" + ($HF_REPO -split "spaces")[1] + ".git"

Write-Host "Deploying to HuggingFace Space..."
Write-Host "Git URL: $HF_GIT_URL"

# Add HuggingFace remote if not exists
git remote get-url huggingface 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote add huggingface $HF_GIT_URL
    Write-Host "Added huggingface remote"
} else {
    git remote set-url huggingface $HF_GIT_URL
    Write-Host "Updated huggingface remote URL"
}

# Push to HuggingFace
Write-Host "Pushing to HuggingFace..."
git push huggingface main

Write-Host ""
Write-Host "✅ Deployment initiated!"
Write-Host "View your Space at: $HF_REPO"
Write-Host ""
Write-Host "Note: First deployment may take 5-10 minutes to build the Docker image."
