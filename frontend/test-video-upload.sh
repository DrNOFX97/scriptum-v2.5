#!/bin/bash

# Test video upload to the API
# This script tests the analyze-video endpoint

VIDEO_FILE="$HOME/Downloads/01_Toy.mp4"
API_URL="http://localhost:5001/analyze-video"

echo "🎬 Testing Video Analysis API"
echo "================================"
echo ""
echo "Video file: $VIDEO_FILE"
echo "API endpoint: $API_URL"
echo ""

# Check if file exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "❌ Error: Video file not found!"
    echo "File path: $VIDEO_FILE"
    exit 1
fi

# Get file size
FILE_SIZE=$(du -h "$VIDEO_FILE" | cut -f1)
echo "File size: $FILE_SIZE"
echo ""

# Make the API request
echo "📤 Uploading video for analysis..."
echo ""

RESPONSE=$(curl -s -X POST "$API_URL" \
  -F "video=@$VIDEO_FILE" \
  -w "\n%{http_code}")

# Extract HTTP status code
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Success! Video analyzed."
    echo ""
    echo "Response:"
    echo "$BODY" | python3 -m json.tool
else
    echo "❌ Error: Request failed"
    echo ""
    echo "Response:"
    echo "$BODY"
fi
