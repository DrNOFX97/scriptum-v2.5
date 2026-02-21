#!/bin/bash

# Test MKV upload to the API
# This script tests MKV file support

VIDEO_FILE="/Users/f.nuno/Desktop/Moshpit/Filmes/Rise.of.the.Footsoldier.Pack.[2007-2023].1080p.BluRay.x264.AC3.(BINGOWINGZ-UKB-RG)/samples/sample4.mkv"
API_URL="http://localhost:5001/analyze-video"

echo "🎬 Testing MKV File Support"
echo "================================"
echo ""
echo "Video file: sample4.mkv"
echo "API endpoint: $API_URL"
echo ""

# Check if file exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "❌ Error: MKV file not found!"
    echo "File path: $VIDEO_FILE"
    exit 1
fi

# Get file size
FILE_SIZE=$(du -h "$VIDEO_FILE" | cut -f1)
echo "File size: $FILE_SIZE"
echo "Format: MKV (Matroska)"
echo ""

# Make the API request
echo "📤 Uploading MKV file for analysis..."
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
    echo "✅ Success! MKV file analyzed."
    echo ""
    echo "Response:"
    echo "$BODY" | python3 -m json.tool
    echo ""
    echo "🎉 MKV support is working!"
else
    echo "❌ Error: Request failed"
    echo ""
    echo "Response:"
    echo "$BODY"
fi
