import json
import os
import sys
import hashlib
import pickle
import traceback

class Config:
    def __init__(self, ccargs):
        self._config_filename = "config.json"
        self._cocodb_filename = "cocodb.pkl"
        self.caches = {}
        self.rebuild_cache = ccargs.rebuild
        self.reload_data = ccargs.rebuild
        self.config = {
            'caches': self.caches
        }
        self.any_uncached_data_loaded = False
        self.reload()
        self.cocodb_cache = os.path.exists(self.cache_path(self._cocodb_filename))

    def reload(self):
        try:    
            if os.path.exists(self._config_filename):
                with open(self._config_filename, 'r') as f:
                    self.config = json.load(f)
                    if 'caches' in self.config: 
                        self.caches = self.config['caches']
                    else: 
                        self.caches = {}
                    print("Loaded config file '" + str(self._config_filename) + "'.")
        except:
            print("Failed to load config file '" + str(self._config_filename) + "'!")
            traceback.print_exc(file=sys.stdout)

    def save(self):
        try:
            with open(self._config_filename, 'w') as f:
                self.config['caches'] = self.caches
                json.dump(self.config, f)
                print("Saved config file '" + str(self._config_filename) + "'.")
        except:
            print("Failed to save config file '" + str(self._config_filename) + "'!")
            traceback.print_exc(file=sys.stdout)

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
        if data:
            mod_time = os.path.getmtime(path)
            path_hash = hashlib.md5(path.encode()).hexdigest()
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
        path_hash = hashlib.md5(path.encode()).hexdigest()
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