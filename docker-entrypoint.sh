#!/bin/bash

echo "Try to apply database migrations"
result=$(aerich upgrade)
if echo "$result" | grep -q "Success upgrade " ||
echo "$result" | grep -q "No upgrade items found"; then
    echo "Migration successful."
else
    echo "Migration failed. Exiting..."
    exit 1
fi

echo "Starting bot"
python -m main
