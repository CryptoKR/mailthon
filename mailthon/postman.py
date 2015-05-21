"""
    mailthon.postman
    ~~~~~~~~~~~~~~~~

    Implements the main Postman class.
"""


from contextlib import contextmanager
from smtplib import SMTP
from .response import SendmailResponse


class Postman:
    """
    Encapsulates a connection to a server and knows
    how to send MIME emails over a certain transport.
    When subclassing, change the ``transport`` and
    ``response_cls`` class variables to tweak the
    transport used and the response class, respectively.

    :param server: The address to a server.
    :param port: Port to connect to.
    :param middlewares: An iterable of middleware that
        will be used by the Postman.
    """

    transport = SMTP
    response_cls = SendmailResponse

    def __init__(self, server, port, middlewares=()):
        self.server = server
        self.port = port
        self.middlewares = list(middlewares)

    def use(self, middleware):
        """
        Use a certain function/class *middleware*,
        i.e. append it to the list of middlewares,
        and return it so it can be used as a
        decorator.
        """
        self.middlewares.append(middleware)
        return middleware

    @contextmanager
    def connection(self):
        """
        A context manager that returns a connection
        to the server using some transport, defaulting
        to SMTP. The transport will be called with
        the server address and port that has been
        passed to the constructor, in that order.
        """
        conn = self.transport(self.server, self.port)
        try:
            conn.ehlo()
            for item in self.middlewares:
                item(conn)
            yield conn
        finally:
            conn.quit()

    def deliver(self, conn, envelope):
        """
        Deliver an *envelope* using a given connection
        *conn*, and return the response object. Does
        not close the connection.
        """
        rejected = conn.sendmail(
            envelope.sender,
            envelope.receivers,
            envelope.to_string(),
        )
        return self.response_cls(conn.noop(), rejected)

    def send_many(self, envelopes):
        """
        Given an iterable of *envelopes*, send them
        all and return a list of response objects.
        """
        with self.connection() as conn:
            return [self.deliver(conn, e) for e in envelopes]

    def send(self, envelope):
        """
        Send one *envelope*. Internally this uses
        the ``send_many`` method.
        """
        return self.send_many([envelope])[0]
