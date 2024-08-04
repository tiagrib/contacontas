import json
import os
import sys
import hashlib
import pickle
import traceback

JSON_INDENT = 4

class Config:
    def __init__(self, ccargs):
        self._config_filename = "config.json"
        self._cache_info_filename = "cache_info.json"
        self._cocodb_filename = "cocodb.pkl"
        self.caches = {}
        self.rebuild_cache = ccargs.rebuild
        self.reload_data = ccargs.rebuild
        self.setup = {}
        self.any_uncached_data_loaded = False
        self.reload()
        self.cocodb_cache = os.path.exists(self.cache_path(self._cocodb_filename))

    def _load_json(self, filename, key = None, description = None):
        desc = description if description else 'json'
        try:    
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    if key:
                        if key in info:
                            info = info[key]
                        else: 
                            info = {}
                    print(f"Loaded {desc} file '" + str(filename) + "'.")
            else:
                info = {}
            return info
        except:
            print(f"Failed to load {desc} file '" + str(filename) + "'!")
            traceback.print_exc(file=sys.stdout)

        
    def _save_json(self, info, filename, key = None, description = None):
        desc = description if description else 'json'
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if key:
                    save_info = {}
                    save_info[key] = info
                else:
                    save_info = info
                json.dump(save_info, f, indent=JSON_INDENT)
                print(f"Saved {desc} file '" + str(filename) + "'.")
        except:
            print(f"Failed to save {desc} file '" + str(filename) + "'!")
            traceback.print_exc(file=sys.stdout)


    def reload(self):
        self.setup = self._load_json(self._config_filename, description='config')
        self.caches = self._load_json(self._cache_info_filename, key='caches', description='config')

    def save(self):
        self._save_json(self.setup, self._config_filename, description='config')
        self._save_json(self.caches, self._cache_info_filename, key='caches', description='cache info')

    def save_cocodb(self, data):
        try:
            cache_filename = self.cache_path(self._cocodb_filename)
            with open(cache_filename, 'wb') as file:
                pickle.dump(data, file)
                print(f'CoCoDb cache saved to "{cache_filename}".')
        except:
            print("Failed to save CoCoDb cache file '" + str(cache_filename) + "'!")
            traceback.print_exc(file=sys.stdout)
    
    def load_cocodb(self):
        try:
            cache_filename = self.cache_path(self._cocodb_filename)
            with open(cache_filename, 'rb') as file:
                data = pickle.load(file)
                file.close()
            print(f'CoCoDb cache loaded from "{cache_filename}".')
            return data
        except:
            print("Failed to load CoCoDb cache file '" + str(cache_filename) + "'!")
            traceback.print_exc(file=sys.stdout)

    def save_source_cache(self, path, data):
        path = str(path)
        if data:
            mod_time = os.path.getmtime(path)
            path_hash = hashlib.md5(str(path).encode()).hexdigest()
            cache_filename = self.cache_path(path_hash)
            if path_hash in self.caches and os.path.exists(cache_filename):
                cache_time = self.caches[path_hash]
                if mod_time == cache_time:
                    return
                
            self.any_uncached_data_loaded = True
            if not os.path.exists(".cache"):
                os.mkdir(".cache")
            
            try:
                with open(cache_filename, 'wb') as file:
                    pickle.dump(data, file)
                    self.caches[path_hash] = mod_time
                    self.save()
                    print(f'Source cache saved to "{cache_filename}".')
            except:
                print("Failed to create Source cache file '" + str(cache_filename) + "'!")
                traceback.print_exc(file=sys.stdout)

    def get_source_cache(self, path):
        if self.rebuild_cache:
            return None
        path_hash = hashlib.md5(str(path).encode()).hexdigest()
        cache_filename = self.cache_path(path_hash)
        if path_hash in self.caches and os.path.exists(cache_filename):
            cache_time = self.caches[path_hash]
            mod_time = os.path.getmtime(path)
            if mod_time == cache_time:
                cache_filename = self.cache_path(path_hash)
                with open(cache_filename, 'rb') as file:
                    data = pickle.load(file)
                    file.close()
                print(f'Source cache loaded from "{cache_filename}".')
                return data
        return None

    def cache_path(self, hash):
        return os.path.join(os.getcwd(), ".cache", hash)