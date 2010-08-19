from aquilon.aqdb.model import Base
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.exc import NoResultFound
from aquilon.exceptions_ import ArgumentError, NotFoundException

class StateEngine:
    transitions = {} # Override in derived class!

    def transition(self, obj, target_state):
        '''Transition to another state.

        host -- the object which wants to change state
        target_state -- a db object referring to the desired state

        returns a list of objects that have changed state.
        throws an ArgumentError exception if the state cannot
        be reached. This method may be subclassed by states
        if there is special logic regarding the transition.
        If the current state has an onLeave method, then the
        method will be called with the object as an argument.
        If the target state has an onEnter method, then the
        method will be called with the object as an argument.

        '''

        if target_state.name == self.name:
            return False

        if target_state.name not in self.__class__.transitions:
            raise ArgumentError("status of %s is invalid" % target_state.name)

        targets = self.__class__.transitions[self.name]
        if target_state.name not in targets:
            raise ArgumentError(("cannot change state to %s from %s. " +
                   "Legal states are: %s") % (target_state.name, self.name,
                   ", ".join(targets)))

        if hasattr(self, 'onLeave'):
            self.onLeave(obj)
        obj.status = target_state
        if hasattr(target_state, 'onEnter'):
            target_state.onEnter(obj)
        return True


    @classmethod
    def get_unique(cls, session, name, **kwargs):
        '''override the Base get_unique to deal with simple polymorphic table

        The API is simpler: only a single positional argument is supported.
        '''

        if not isinstance(session, Session):
            raise TypeError("The first argument of %s() must be an "
                            "SQLAlchemy session." % caller)

        compel = kwargs.get('compel', False)
        preclude = kwargs.pop('preclude', False)
        clslabel = "state"

        if name not in cls.transitions:
            if not compel:
                return None
            msg = "%s %s not found." % (clslabel, name)
            raise NotFoundException(msg)
            
        query = session.query(cls).filter(getattr(cls, "name") == name)
        # We can't get NoResultFound since we've already checked the transition
        # table, and we can't get MultipleResultsFound since name is unique.
        obj = query.one()
        if preclude:
            msg = "%s %s already exists." % (clslabel, name)
            raise ArgumentError(msg)
        return obj

