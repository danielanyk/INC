const client = new Mongo("mongodb://localhost:27017");
// const client = new Mongo("mongodb+srv://admin:admin1@test-database.jnlzfbh.mongodb.net/?retryWrites=true&w=majority&appName=test-database")
target_db = "FYP"
const db = client.getDB(target_db);
db.dropDatabase();
print(`Database '${target_db}' dropped.`);
db.createCollection("users", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            title: "User Object Validation",
            required: ["username", "name", "password_hash", "perm"],
            properties: {
                username: {
                    bsonType: "string",
                    description: "'username' must be a string and is required"
                },
                name: {
                    bsonType: "string",
                    description: "'name' must be a string and is required"
                },
                password_hash: {
                    bsonType: "string",
                    description: "'password_hash' must be a string and is required"
                },
                perm: {
                    bsonType: "string",
                    description: "'perm' must be a string and is required"
                }
            }
        }
    }
})

db.createCollection("batch", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            title: "Batch Object Validation",
            required: ["batchID", "batchPath", "userID", "batchStartProcessing", "batchFinishProcessing", "status", "totalFrames", "framesProcessed"],
            properties: {
                batchID: {
                    bsonType: "int",
                    description: "'batchID' must be a int (64-bit) integer and is required"
                },
                batchPath: {
                    bsonType: "string",
                    description: "'batchPath' must be a string and is required"
                },
                userID: {
                    bsonType: "int",
                    description: "'userID' must be a int (64-bit) integer and is required"
                },
                batchStartProcessing: {
                    bsonType: "string",
                    description: "'batchStartProcessing' must be a string and is required"
                },
                batchFinishProcessing: {
                    bsonType: "string",
                    description: "'batchFinishProcessing' must be a string and is required"
                },
                status: {
                    bsonType: "string",
                    description: "'status' must be a string and is required"
                },
                totalFrames: {
                    bsonType: "int",
                    description: "'totalFrames' must be a int (64-bit) integer and is required"
                },
                framesProcessed: {
                    bsonType: "int",
                    description: "'framesProcessed' must be a int (64-bit) integer and is required"
                }
            }
        }
    }
})

db.createCollection("batchImage", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            title: "Batch Image Object Validation",
            required: ["batchID", "imageID"],
            properties: {
                batchID: {
                    bsonType: "int",
                    description: "'batchID' must be a int (64-bit) integer and is required"
                },
                imageID: {
                    bsonType: "int",
                    description: "'imageID' must be a int (64-bit) integer and is required"
                }
            }
        }
    }
})

db.createCollection("image", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            title: "Image Object Validation",
            required: ["imageID", "imagePath", "latitude", "longitude", "town", "road", "roadType", "datetime"],
            properties: {
                imageID: {
                    bsonType: "int",
                    description: "'imageID' must be a int (64-bit) integer and is required"
                },
                imagePath: {
                    bsonType: "string",
                    description: "'imagePath' must be a string and is required"
                },
                latitude: {
                    bsonType: "double",
                    description: "'latitude' must be a double and is required, within 1.470056 and 1.159486 deg. north"
                },
                longitude: {
                    bsonType: "double",
                    description: "'longitude' must be a double and is required, within 104.4061149 and 103.604572 deg. east"
                },
                town: {
                    bsonType: "string",
                    description: "'town' must be a string and is required"
                },
                road: {
                    bsonType: "string",
                    description: "'road' must be a string and is required"
                },
                roadType: {
                    bsonType: "string",
                    description: "'roadType' must be a string and is required"
                },
                datetime: {
                    bsonType: "string",
                    description: "'datetime' must be a string and is required"
                }
            }
        }
    }
})

db.createCollection("defect", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            title: "Defect Object Validation",
            required: ["defectID", "imageID", "outputLabel", "confidence", "bbox", "severity"],
            properties: {
                defectID: {
                    bsonType: "int",
                    description: "'defectID' must be a int (64-bit) integer and is required"
                },
                imageID: {
                    bsonType: "int",
                    description: "'imageID' must be a int (64-bit) integer and is required"
                },
                outputLabel: {
                    bsonType: "string",
                    description: "'outputLabel' must be a string and is required"
                },
                typeID: {
                    bsonType: "int",
                    description: "'typeID' must be a int (64-bit) integer. Must be filled when pre-processed."
                },
                confidence: {
                    bsonType: ["double", "decimal", "int"],
                    description: "'confidence' must be a double,decimal or integer and is required, between 0.00 and 1.00"
                },
                bbox: {
                    bsonType: "string",
                    description: "'bbox' must be an array and is required"
                },
                severity: {
                    bsonType: "int",
                    description: "'severity' must be a int (64-bit) integer and is required"
                }
            }
        }
    }
})

db.createCollection("report", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            title: "Report Object Validation",
            required: ["reportID", "imageID", "inspectedBy", "inspectionDate", "generationTime", "reportPath", "tags"],
            properties: {
                reportID: {
                    bsonType: "int",
                    description: "'reportID' must be a int (64-bit) integer and is required"
                },
                imageID: {
                    bsonType: "int",
                    description: "'imageID' must be a int (64-bit) integer and is required"
                },
                inspectedBy: {
                    bsonType: "string",
                    description: "'inspectedBy' must be a string and is required"
                },
                inspectionDate: {
                    bsonType: "string",
                    description: "'inspectionDate' must be a string and is required"
                },
                generationTime: {
                    bsonType: "string",
                    description: "'generationTime' must be a string and is required"
                },
                reportPath: {
                    bsonType: "string",
                    description: "'reportPath' must be a string and is required"
                },
                tags: {
                    bsonType: "string",
                    description: "'tags' must be a string and is required"
                },
                quantity: {
                    bsonType: "string",
                    description: "'quantity' can be of string type and is optional"
                },
                measurement: {
                    bsonType: "string",
                    description: "'measurement' can be of string type and is optional"
                },
                causeOfDefect: {
                    bsonType: "string",
                    description: "'cause of defect' can be of string type and is optional"
                },
                recommendations: {
                    bsonType: "string",
                    description: "'recommendations' can be of string type and is optional"
                },
                remarks: {
                    bsonType: "string",
                    description: "'remarks' can be of string type and is optional"
                },
                reportedVia: {
                    bsonType: "string",
                    description: "'reported via' can be of string type and is optional"
                },
                acknowledgement: {
                    bsonType: "string",
                    description: "'acknowledgement' can be of string type and is optional"
                }
            }
        }
    }
})


db.createCollection("defectType", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            title: "Defect Type Object Validation",
            required: ["typeID", "type"],
            properties: {
                typeID: {
                    bsonType: "int",
                    description: "'typeID' must be a int (64-bit) integer and is required"
                },
                type: {
                    bsonType: "string",
                    description: "'type' must be a string and is required"
                }
            }
        }
    }
})

const fs = require('fs');
const path = require('path');

// Ensure `mongo` environment has access to `__dirname`
const __dirname = path.resolve();

const collections = ["users", "defectType"];

collections.forEach(collectionName => {
    const filePath = path.join(__dirname, 'Data', `${collectionName}.json`);
    const jsonDataString = fs.readFileSync(filePath).toString();
    const jsonData = JSON.parse(jsonDataString);
    try {
        jsonData.forEach(document => {
            printjson(document);
            delete document._id;
            db[collectionName].insertOne(document);
        });
    } catch (e) {
        print(e);
    }
});
print(`Database '${target_db}' successfully recreated.`);



