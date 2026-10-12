"""Hand-written administrative adjacency; needs human review before modelling.

Kyiv City links only to its enclosing Kyivska oblast. Excluded Luhanska/Crimea
are absent. No alert correlations were used to define edges.
"""

NEIGHBORS: dict[str, tuple[str, ...]] = {
    'Cherkaska oblast': ('Kirovohradska oblast', 'Kyivska oblast', 'Poltavska oblast', 'Vinnytska oblast'),
    'Chernihivska oblast': ('Kyivska oblast', 'Poltavska oblast', 'Sumska oblast'),
    'Chernivetska oblast': ('Ivano-Frankivska oblast', 'Khmelnytska oblast', 'Ternopilska oblast', 'Vinnytska oblast'),
    'Dnipropetrovska oblast': ('Donetska oblast', 'Kharkivska oblast', 'Khersonska oblast', 'Kirovohradska oblast', 'Mykolaivska oblast', 'Poltavska oblast', 'Zaporizka oblast'),
    'Donetska oblast': ('Dnipropetrovska oblast', 'Kharkivska oblast', 'Zaporizka oblast'),
    'Ivano-Frankivska oblast': ('Chernivetska oblast', 'Lvivska oblast', 'Ternopilska oblast', 'Zakarpatska oblast'),
    'Kharkivska oblast': ('Dnipropetrovska oblast', 'Donetska oblast', 'Poltavska oblast', 'Sumska oblast'),
    'Khersonska oblast': ('Dnipropetrovska oblast', 'Mykolaivska oblast', 'Zaporizka oblast'),
    'Khmelnytska oblast': ('Chernivetska oblast', 'Rivnenska oblast', 'Ternopilska oblast', 'Vinnytska oblast', 'Zhytomyrska oblast'),
    'Kirovohradska oblast': ('Cherkaska oblast', 'Dnipropetrovska oblast', 'Mykolaivska oblast', 'Odeska oblast', 'Poltavska oblast', 'Vinnytska oblast'),
    'Kyiv City': ('Kyivska oblast',),
    'Kyivska oblast': ('Cherkaska oblast', 'Chernihivska oblast', 'Kyiv City', 'Poltavska oblast', 'Vinnytska oblast', 'Zhytomyrska oblast'),
    'Lvivska oblast': ('Ivano-Frankivska oblast', 'Rivnenska oblast', 'Ternopilska oblast', 'Volynska oblast', 'Zakarpatska oblast'),
    'Mykolaivska oblast': ('Dnipropetrovska oblast', 'Khersonska oblast', 'Kirovohradska oblast', 'Odeska oblast'),
    'Odeska oblast': ('Kirovohradska oblast', 'Mykolaivska oblast', 'Vinnytska oblast'),
    'Poltavska oblast': ('Cherkaska oblast', 'Chernihivska oblast', 'Dnipropetrovska oblast', 'Kharkivska oblast', 'Kirovohradska oblast', 'Kyivska oblast', 'Sumska oblast'),
    'Rivnenska oblast': ('Khmelnytska oblast', 'Lvivska oblast', 'Ternopilska oblast', 'Volynska oblast', 'Zhytomyrska oblast'),
    'Sumska oblast': ('Chernihivska oblast', 'Kharkivska oblast', 'Poltavska oblast'),
    'Ternopilska oblast': ('Chernivetska oblast', 'Ivano-Frankivska oblast', 'Khmelnytska oblast', 'Lvivska oblast', 'Rivnenska oblast'),
    'Vinnytska oblast': ('Cherkaska oblast', 'Chernivetska oblast', 'Khmelnytska oblast', 'Kirovohradska oblast', 'Kyivska oblast', 'Odeska oblast', 'Zhytomyrska oblast'),
    'Volynska oblast': ('Lvivska oblast', 'Rivnenska oblast'),
    'Zakarpatska oblast': ('Ivano-Frankivska oblast', 'Lvivska oblast'),
    'Zaporizka oblast': ('Dnipropetrovska oblast', 'Donetska oblast', 'Khersonska oblast'),
    'Zhytomyrska oblast': ('Khmelnytska oblast', 'Kyivska oblast', 'Rivnenska oblast', 'Vinnytska oblast'),
}


def validate_neighbors(oblasts: list[str], neighbors: dict[str, tuple[str, ...]] = NEIGHBORS) -> None:
    """Require exact geography, nonempty symmetric edges and no self-links."""
    if set(oblasts) != set(neighbors):
        raise ValueError("Neighbor keys must match panel oblast names exactly")
    for oblast, adjacent in neighbors.items():
        if not adjacent or oblast in adjacent or len(adjacent) != len(set(adjacent)):
            raise ValueError("Neighbors must be nonempty, unique, and exclude self")
        for other in adjacent:
            if other not in neighbors or oblast not in neighbors[other]:
                raise ValueError("Neighbor edges must be symmetric and inside the panel")
