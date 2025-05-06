#***********************************************************************
# MODULE: mongo_db_handler
# SCOPE:  Interface between API and Mongo DB
# REV: 1.0 - Integrated MongoDB handler for database interaction.
#
# Created by: Codreanu Dan
# Descr: This module provides the communication between the diag API
#        and MongoDB. It includes connection handling, document insertion.
#***********************************************************************

#***********************************************************************
# IMPORTS:
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

#***********************************************************************
# DEFINES:
CONNECTION_STRING = \
"mongodb+srv://dbUser:dbUserPassword@cluster0.wtnbkwh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tls=true&tlsAllowInvalidCertificates=true"
# "mongodb+srv://dbUser:dbUserPassword@cluster0.wtnbkwh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tls=true&tlsAllowInvalidCertificates=true"
DATABASE_NAME = "DIAG_API_DATABASE"
COLLECTION_NAME = "DIAG_API_DATABASE_COLLECTION"

#***********************************************************************
# MongoDBHandler Class
# Handles the MongoDB connection and database interactions
#***********************************************************************
class MongoDBHandler:
    def __init__(self, uri, db_name, collection_name):
        """
        Initializes the MongoDBHandler class with the provided connection
        URI, database name, and collection name.

        Parameters:
            uri (str): The MongoDB connection URI.
            db_name (str): The name of the database to connect to.
            collection_name (str): The name of the collection to interact with.
        """
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.is_connected = False

        # Attempt to connect to MongoDB
        self.connect_to_mongo_db()
    
    #*******************************************************************
    # Tool functions 
    
    def init_mongo_connection(self, uri:str) -> None:
        client = MongoClient(uri)
        try:
            client.admin.command("ping")
            print("[MONGO_DB][INFO][✅] Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print("[MONGO_DB][ERROR][❌] Could not connect to MongoDB:", e)
            raise
        return client

    def connect_to_mongo_db(self):
        """Attempts to connect to MongoDB using the provided URI."""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            self.is_connected = True
            print("[MONGO_DB][INFO][✅] Successfully connected to MongoDB!")
        except (ConnectionFailure, OperationFailure) as e:
            self.is_connected = False
            print(f"[MONGO_DB][INFO][❌] Error: {e}")
    
    # END of Tool functions 
    #*******************************************************************
    
    #*******************************************************************
    # Functions used in API verbs
    
    ''' POST '''
    def post_snapshot_data_to_db(self, document):
        """
        Inserts a document into the MongoDB collection.

        Parameters:
            document (dict): The document to be inserted into the collection.

        Returns:
            The inserted document's ID, or None if the insertion fails.
        """
        if not self.is_connected:
            print("Error: Not connected to MongoDB.")
            return None
        
        try:
            result = self.collection.insert_one(document)
            print(f"[MONGO_DB][INFO][✅] Document inserted with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            print(f"[MONGO_DB][INFO][❌] Error inserting document: {e}")
            return None
       
    ''' GET ''' 
    def get_snapshot_data_from_db(self, snapshot_id=None):
        """
        Retrieves snapshot data from MongoDB collection.
        
        Parameters:
            snapshot_id (str, optional): If provided, retrieves a specific snapshot.
                                        If None, retrieves all snapshots.
        
        Returns:
            A list of snapshots or a single snapshot if snapshot_id is provided.
            Returns None if an error occurs or no matching snapshots are found.
        """
        if not self.is_connected:
            print("Error: Not connected to MongoDB.")
            return None
        
        try:
            if snapshot_id:
                # Search for a document with a specific DIAG_SNAPSHOT_XXX key or by report_id
                # This handles both full IDs (DIAG_SNAPSHOT_DIAG_20250504_2351) and 
                # partial IDs (20250504_2351)
                
                # First try exact match on full key
                snapshot_key = f"DIAG_SNAPSHOT_DIAG_{snapshot_id}" if not snapshot_id.startswith("DIAG_") else snapshot_id
                if not snapshot_key.startswith("DIAG_SNAPSHOT_"):
                    snapshot_key = f"DIAG_SNAPSHOT_{snapshot_key}"
                    
                # Try direct key lookup first
                snapshot = self.collection.find_one({snapshot_key: {"$exists": True}})
                
                # If not found, try searching by report_id inside any DIAG_SNAPSHOT field
                if not snapshot:
                    # Extract date part if full format provided
                    search_term = snapshot_id
                    if "DIAG_SNAPSHOT_DIAG_" in snapshot_id:
                        search_term = snapshot_id.replace("DIAG_SNAPSHOT_DIAG_", "")
                    elif "DIAG_" in snapshot_id:
                        search_term = snapshot_id.replace("DIAG_", "")
                    
                    # Try multiple search patterns
                    query = {"$or": [
                        # Search in any field with report_id 
                        {f"DIAG_SNAPSHOT_DIAG_{search_term}.report_id": {"$exists": True}},
                        {"DIAG_SNAPSHOT_DIAG_20250504_2351.report_id": {"$regex": search_term}},
                        {"DIAG_SNAPSHOT_DIAG_20250505_0006.report_id": {"$regex": search_term}}
                    ]}
                    snapshot = self.collection.find_one(query)
                
                if snapshot:
                    print(f"[MONGO_DB][INFO][✅] Retrieved snapshot with ID: {snapshot_id}")
                    return snapshot
                else:
                    print(f"[MONGO_DB][INFO][❌] No snapshot found with ID: {snapshot_id}")
                    return None
            else:
                # # Return all snapshots, but limit to most recent 100
                # snapshots = list(self.collection.find().sort("_id", -1).limit(100))
                # print(f"[MONGO_DB][INFO][✅] Retrieved {len(snapshots)} snapshots")
                # return snapshots
                pass
                
        except Exception as e:
            print(f"[MONGO_DB][INFO][❌] Error retrieving snapshot(s): {e}")
            return None
    
    def get_field_from_snapshot(self, snapshot_id: str, snapshot_param: str):
        """
        Retrieves a specific field from a diagnostic snapshot document using dot notation (e.g., error_memory.ign_stat).

        :param snapshot_id: ID of the snapshot
        :param snapshot_param: Dot-notated path to the field (e.g., "error_memory.ign_stat")
        :return: The value of the field or None if not found
        """
        snapshot = self.get_snapshot_data_from_db(snapshot_id)
        if not snapshot:
            print(f"[MONGO_DB][INFO][❌] Snapshot '{snapshot_id}' not found.")
            return None

        # Convert ObjectId to string for serialization
        if '_id' in snapshot:
            snapshot['_id'] = str(snapshot['_id'])

        # Step 1: Go to the root diagnostic snapshot key (e.g., "DIAG_SNAPSHOT_DIAG_20250504_2351")
        diag_snapshot_key = None
        for key in snapshot:
            if key.startswith("DIAG_SNAPSHOT_DIAG_"):
                diag_snapshot_key = key
                break

        if not diag_snapshot_key:
            print(f"[MONGO_DB][INFO][❌] No diagnostic snapshot key found in snapshot '{snapshot_id}'.")
            return None

        # Step 2: Traverse into the snapshot and look for the field
        data = snapshot[diag_snapshot_key]
        try:
            for part in snapshot_param.split('.'):
                data = data[part]
            print(f"[MONGO_DB][INFO][✅] Found field '{snapshot_param}' in snapshot.")
            return data
        except (KeyError, TypeError):
            print(f"[MONGO_DB][INFO][❌] Field '{snapshot_param}' not found in snapshot.")
            return None
      
    ''' DELETE '''
    def delete_snapshot_from_db(self, snapshot_id):
        """
        Deletes a snapshot from MongoDB collection.
        
        Parameters:
            snapshot_id (str): ID of the snapshot to delete
        
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if not self.is_connected:
            print("Error: Not connected to MongoDB.")
            return False
        
        try:
            # Format the key if needed
            snapshot_key = snapshot_id
            if not snapshot_id.startswith("DIAG_SNAPSHOT_"):
                if snapshot_id.startswith("DIAG_"):
                    snapshot_key = f"DIAG_SNAPSHOT_{snapshot_id}"
                else:
                    snapshot_key = f"DIAG_SNAPSHOT_DIAG_{snapshot_id}"
            
            # Try to find the document first
            snapshot = self.collection.find_one({snapshot_key: {"$exists": True}})
            
            # If not found by key, try by report_id inside any DIAG_SNAPSHOT
            if not snapshot:
                # Extract date part if full format provided
                search_term = snapshot_id
                if "DIAG_SNAPSHOT_DIAG_" in snapshot_id:
                    search_term = snapshot_id.replace("DIAG_SNAPSHOT_DIAG_", "")
                elif "DIAG_" in snapshot_id:
                    search_term = snapshot_id.replace("DIAG_", "")
                
                # Try by report_id field
                query = {"$or": [
                    {f"{key}.report_id": search_term} for key in self.collection.find_one().keys() 
                    if key.startswith("DIAG_SNAPSHOT_")
                ]}
                snapshot = self.collection.find_one(query)
            
            if snapshot:
                # Delete the document
                result = self.collection.delete_one({"_id": snapshot["_id"]})
                if result.deleted_count > 0:
                    print(f"[MONGO_DB][INFO][✅] Deleted snapshot with ID: {snapshot_id}")
                    return True
                else:
                    print(f"[MONGO_DB][INFO][❌] Failed to delete snapshot with ID: {snapshot_id}")
                    return False
            else:
                print(f"[MONGO_DB][INFO][❌] No snapshot found with ID: {snapshot_id}")
                return False
                
        except Exception as e:
            print(f"[MONGO_DB][INFO][❌] Error deleting snapshot: {e}")
            return False

    def delete_field_from_snapshot(self, snapshot_id, field_path):
        """
        Deletes a specific field from a snapshot.
        
        Parameters:
            snapshot_id (str): ID of the snapshot
            field_path (str): Path to the field to delete (e.g. "coolant_temp" or "security_access.auth_request")
        
        Returns:
            bool: True if updated successfully, False otherwise
        """
        if not self.is_connected:
            print("Error: Not connected to MongoDB.")
            return False
        
        try:
            # Find the snapshot first to determine the correct key
            snapshot = None
            diag_key = None
            
            # Try different formats to find the document
            possible_formats = [
                snapshot_id,
                f"DIAG_SNAPSHOT_{snapshot_id}",
                f"DIAG_SNAPSHOT_DIAG_{snapshot_id}"
            ]
            
            # If snapshot_id already starts with a prefix, don't duplicate it
            if snapshot_id.startswith("DIAG_SNAPSHOT_"):
                possible_formats = [snapshot_id]
            elif snapshot_id.startswith("DIAG_"):
                possible_formats = [snapshot_id, f"DIAG_SNAPSHOT_{snapshot_id}"]
            
            # Try each format
            for format_id in possible_formats:
                query = {format_id: {"$exists": True}}
                snapshot = self.collection.find_one(query)
                if snapshot:
                    diag_key = format_id
                    break
            
            # If not found by direct key, try by report_id
            if not snapshot:
                # Extract date part if full format provided
                search_term = snapshot_id
                if "DIAG_SNAPSHOT_DIAG_" in snapshot_id:
                    search_term = snapshot_id.replace("DIAG_SNAPSHOT_DIAG_", "")
                elif "DIAG_" in snapshot_id:
                    search_term = snapshot_id.replace("DIAG_", "")
                
                # Find documents with matching report_id in any DIAG_SNAPSHOT field
                for key in self.collection.find_one().keys():
                    if key.startswith("DIAG_SNAPSHOT_"):
                        query = {f"{key}.report_id": search_term}
                        snapshot = self.collection.find_one(query)
                        if snapshot:
                            diag_key = key
                            break
            
            if snapshot and diag_key:
                # Build the field path for the update
                update_path = f"{diag_key}.{field_path}"
                
                # Use $unset to remove the field
                result = self.collection.update_one(
                    {"_id": snapshot["_id"]},
                    {"$unset": {update_path: ""}}
                )
                
                if result.modified_count > 0:
                    print(f"[MONGO_DB][INFO][✅] Deleted field {field_path} from snapshot {snapshot_id}")
                    return True
                else:
                    print(f"[MONGO_DB][INFO][❌] Field {field_path} not found in snapshot {snapshot_id}")
                    return False
            else:
                print(f"[MONGO_DB][INFO][❌] No snapshot found with ID: {snapshot_id}")
                return False
                
        except Exception as e:
            print(f"[MONGO_DB][INFO][❌] Error deleting field from snapshot: {e}")
            return False
        
    ''' PUT '''
    def put_snapshot_in_db(self, snapshot_id, update_data):
        """
        Updates a snapshot in MongoDB collection.
        
        Parameters:
            snapshot_id (str): ID of the snapshot to update
            update_data (dict): New data to update in the snapshot
        
        Returns:
            bool: True if updated successfully, False otherwise
        """
        if not self.is_connected:
            print("Error: Not connected to MongoDB.")
            return False
        
        try:
            # Format the key if needed
            snapshot_key = snapshot_id
            if not snapshot_id.startswith("DIAG_SNAPSHOT_"):
                if snapshot_id.startswith("DIAG_"):
                    snapshot_key = f"DIAG_SNAPSHOT_{snapshot_id}"
                else:
                    snapshot_key = f"DIAG_SNAPSHOT_DIAG_{snapshot_id}"
            
            # Try to find the document first
            snapshot = self.collection.find_one({snapshot_key: {"$exists": True}})
            
            # If not found by key, try by report_id inside any DIAG_SNAPSHOT
            if not snapshot:
                # Extract date part if full format provided
                search_term = snapshot_id
                if "DIAG_SNAPSHOT_DIAG_" in snapshot_id:
                    search_term = snapshot_id.replace("DIAG_SNAPSHOT_DIAG_", "")
                elif "DIAG_" in snapshot_id:
                    search_term = snapshot_id.replace("DIAG_", "")
                
                # Try multiple search patterns
                query = {"$or": [
                    # Search in any field with report_id 
                    {f"DIAG_SNAPSHOT_DIAG_{search_term}.report_id": {"$exists": True}},
                    {"DIAG_SNAPSHOT_DIAG_20250504_2351.report_id": {"$regex": search_term}},
                    {"DIAG_SNAPSHOT_DIAG_20250505_0006.report_id": {"$regex": search_term}}
                ]}
                snapshot = self.collection.find_one(query)
            
            if snapshot:
                # Find the actual key for the snapshot data
                diag_key = None
                for key in snapshot.keys():
                    if key.startswith("DIAG_SNAPSHOT_"):
                        diag_key = key
                        break
                
                if not diag_key:
                    print(f"[MONGO_DB][INFO][❌] Could not find DIAG_SNAPSHOT key in document")
                    return False
                
                # Prepare update operations
                update_operations = {}
                for field, value in update_data.items():
                    update_operations[f"{diag_key}.{field}"] = value
                
                # Update the document
                result = self.collection.update_one(
                    {"_id": snapshot["_id"]},
                    {"$set": update_operations}
                )
                
                if result.modified_count > 0:
                    print(f"[MONGO_DB][INFO][✅] Updated snapshot with ID: {snapshot_id}")
                    return True
                else:
                    print(f"[MONGO_DB][INFO][❌] No changes made to snapshot with ID: {snapshot_id}")
                    return False
            else:
                print(f"[MONGO_DB][INFO][❌] No snapshot found with ID: {snapshot_id}")
                return False
                
        except Exception as e:
            print(f"[MONGO_DB][INFO][❌] Error updating snapshot: {e}")
            return False
        
    # END of Functions used in API verbs
    #*******************************************************************


