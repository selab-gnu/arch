from .property_change import PropertyChangeListener, PropertyChangeSupport


class Model:
    """데이터(party, votes)를 보관하고, 값이 바뀌면 리스너(View, Controller)에게 알린다."""

    def __init__(self) -> None:
        self._support = PropertyChangeSupport(self)
        self.party = "none"
        self.votes = 0

    def add_property_change_listener(self, pcl: PropertyChangeListener) -> None:
        self._support.add_property_change_listener(pcl)

    def remove_property_change_listener(self, pcl: PropertyChangeListener) -> None:
        self._support.remove_property_change_listener(pcl)

    def set_votes(self, votes: int) -> None:
        prev_votes = self.votes
        self.votes = votes
        self._support.fire_property_change("votes", prev_votes, votes)

    def set_party(self, party: str) -> None:
        prev_party = self.party
        self.party = party
        self._support.fire_property_change("party", prev_party, party)
