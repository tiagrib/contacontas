from .manipulation import append_tag, TAGS_FIELD

class classifier_stack:
    def __init__(self):
        self.stack = []

    def add_classifier(self, c):
        self.stack.append(c)

    def run(self, data):
        for c in self.stack:
            data = c.run(data)
        return data

class t_contains_words():
    def __init__(self, field, keywords):
        self.field = field
        self.keywords = keywords
        if not isinstance(self.keywords, list):
            self.keywords = [keywords]

    def test(self, rec):
        for k in self.keywords:
            if k in rec[self.field]: return True
        return False
    

class t_eq():
    def __init__(self, field, test_value):
        self.field = field
        self.test_value = test_value

    def test(self, rec):
        return rec[self.field] == self.test_value
    
class t_lessthan():
    def __init__(self, field, test_value):
        self.field = field
        self.test_value = test_value

    def test(self, rec):
        return rec[self.field] < self.test_value
    
class t_greaterthan():
    def __init__(self, field, test_value):
        self.field = field
        self.test_value = test_value

    def test(self, rec):
        return rec[self.field] > self.test_value
    
class t_not():
    def __init__(self, orig_test):
        self.orig_test = orig_test

    def test(self, rec):
        return not self.orig_test.test(rec)
    
class t_and():
    def __init__(self, test1, test2):
        self.test1 = test1
        self.test2 = test2

    def test(self, rec):
        return self.test1.test(rec) and self.test2.test(rec)
    
class t_or():
    def __init__(self, test1, test2):
        self.test1 = test1
        self.test2 = test2

    def test(self, rec):
        return self.test1.test(rec) or self.test2.test(rec)

class test_classifier:
    def __init__(self, classes = {}):
        self.test_classes = classes

    def add_class(self, test, tag):
        self.test_classes[test] = tag

    def run(self, data):
        return data.apply(lambda rec : self.exec(rec), axis=1, result_type='broadcast')

    def test(self, rec):
        for class_test, tag in self.test_classes.items():
            if class_test.test(rec): 
                return tag
        return None

    def exec(self, rec):
        tag = self.test(rec)
        if tag:
            rec[TAGS_FIELD] = append_tag(rec, tag)
        return rec