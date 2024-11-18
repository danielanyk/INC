// clearFolder.js
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Function to clear a folder
function clearFolder(folderPath) {
    try {
        // Delete all files
        execSync(`del /q "${folderPath}\\*.*"`, { stdio: 'ignore' });

        // Delete all subdirectories
        execSync(`rmdir /s /q "${folderPath}\\."`, { stdio: 'ignore' });
    } catch (error) {
        console.error(`Failed to clear folder ${folderPath}. Reason: ${error.message}`);
    }

    execSync(`mkdir "${folderPath}"`, { stdio: 'ignore' });
    execSync(`mkdir "${path.join(folderPath, "unedited")}"`, { stdio: 'ignore' });
    execSync(`mkdir "${path.join(folderPath, "classified")}"`, { stdio: 'ignore' });
    execSync(`mkdir "${path.join(folderPath, "classified", "train")}"`, { stdio: 'ignore' });
    execSync(`mkdir "${path.join(folderPath, "classified", "train", "s1")}"`, { stdio: 'ignore' });
    execSync(`mkdir "${path.join(folderPath, "classified", "train", "s2")}"`, { stdio: 'ignore' });
    execSync(`mkdir "${path.join(folderPath, "classified", "train", "s3")}"`, { stdio: 'ignore' });
}

// Specify the folder to clear
const folderToClear = path.join(__dirname, '../../active_learning');
console.log(folderToClear);

// Clear the folder
clearFolder(folderToClear);
