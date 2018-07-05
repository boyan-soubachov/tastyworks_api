# TODO: This whole design needs to be refactored. We need an architecture that allows
# TastyAPISession to be the underlying to all model objects *as an instance* rather
# than a class.
# There is also a 1 to many relationship between a tasty session and (orders, accounts, etc...)


class Model(object):
    def set_session(self, session):
        if not session.logged_in:
            raise Exception('Setting order to non-active session')
        self.session = session
