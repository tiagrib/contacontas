import hashlib


def create_record_hash(bank, account, date, value, desc):
    sha = hashlib.md5(str((bank, account, date, value, desc)).encode("utf-8"))
    return sha.hexdigest()


class CDDatabase:
    def __init__(self):
        pass

    def load_bank(self, bank):
        raise NotImplementedError()

    def finalize_loading(self):
        raise NotImplementedError()

    def postprocess(self):
        raise NotImplementedError()

    def make_records_from_tagged(self, tag, bank_account, invert_value=False, new_tag=""):
        raise NotImplementedError()
