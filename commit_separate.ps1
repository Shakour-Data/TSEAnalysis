# Get the list of changed files
$status = git status --porcelain

# Loop through each line
$status -split "`n" | ForEach-Object {
    $line = $_.Trim()
    if ($line -match '^(.{2})\s+(.+)$') {
        $statusCode = $matches[1]
        $file = $matches[2]

        # Determine the commit message based on status
        switch ($statusCode) {
            'M ' { $message = "Update $file" }
            'D ' { $message = "Delete $file" }
            '??' { $message = "Add $file" }
            default { $message = "Change $file" }
        }

        # Stage the file
        git add "$file"

        # Commit the file
        git commit -m "$message"
    }
}