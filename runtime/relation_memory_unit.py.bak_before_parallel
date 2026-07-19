#!/usr/bin/env python3
"""
==========================================================================
IFÁ Processor V4.5

Relation Memory Unit (RMU)
==========================================================================

The RMU is the native storage for RelationFrame objects.

It replaces direct dictionary access.

Responsibilities
----------------

Store frames

Lookup by relation id

Lookup by destination

Track producer/broadcast mapping

Provide statistics
"""

from __future__ import annotations

from dataclasses import dataclass

from runtime.relation_frame import RelationFrame
from compiler.relation_reference import RelationReference


class RelationAbsent(RuntimeError):
    pass


class DuplicateRelation(RuntimeError):
    pass


@dataclass
class RMUStatistics:

    frames: int = 0

    destinations: int = 0

    fetches: int = 0

    broadcasts: int = 0


class RelationMemoryUnit:

    def __init__(self):

        self.frames = {}

        self.destination_map = {}

        self.stats = RMUStatistics()

    # ----------------------------------------------------------

    def clear(self):

        self.frames.clear()

        self.destination_map.clear()

        self.stats = RMUStatistics()

    # ----------------------------------------------------------

    def store(
        self,
        frame: RelationFrame,
        destinations,
    ):

        if frame.relation_id in self.frames:

            raise DuplicateRelation(
                frame.relation_id
            )

        self.frames[
            frame.relation_id
        ] = frame

        self.stats.frames += 1

        for destination in destinations:

            self.destination_map[
                destination
            ] = RelationReference(
                producer=frame.relation_id,
                destination=destination,
            )

            self.stats.destinations += 1

            self.stats.broadcasts += 1

    # ----------------------------------------------------------

    def fetch(
        self,
        relation_id,
    ) -> RelationFrame:

        self.stats.fetches += 1

        if relation_id not in self.frames:

            raise RelationAbsent(
                relation_id
            )

        return self.frames[
            relation_id
        ]

    # ----------------------------------------------------------

    def fetch_by_destination(
        self,
        destination,
    ) -> RelationFrame:

        if destination not in self.destination_map:

            raise RelationAbsent(
                destination
            )

        ref = self.destination_map[
            destination
        ]

        return self.fetch(
            ref.producer
        )

    # ----------------------------------------------------------

    def relation_result(
        self,
        relation_id,
    ):

        return self.fetch(
            relation_id
        ).VALUE

    # ----------------------------------------------------------

    def destination_result(
        self,
        destination,
    ):

        return self.fetch_by_destination(
            destination
        ).VALUE

    # ----------------------------------------------------------

    def relation_exists(
        self,
        relation_id,
    ):

        return relation_id in self.frames

    # ----------------------------------------------------------

    def destination_exists(
        self,
        destination,
    ):

        return destination in self.destination_map

    # ----------------------------------------------------------

    def summary(self):

        return {

            "frames":

                self.stats.frames,

            "destinations":

                self.stats.destinations,

            "fetches":

                self.stats.fetches,

            "broadcasts":

                self.stats.broadcasts,

        }


if __name__ == "__main__":

    from runtime.frame_builder import (
        build_relation_frame
    )

    rmu = RelationMemoryUnit()

    frame = build_relation_frame(

        "R0",

        "PAPO",

        2,

        3,

        5,

    )

    rmu.store(

        frame,

        [

            "A",

            "A_COPY",

        ],

    )

    print(

        "Fetch R0"

    )

    print(

        rmu.fetch(

            "R0"

        )

    )

    print()

    print(

        "Fetch A"

    )

    print(

        rmu.fetch_by_destination(

            "A"

        )

    )

    print()

    print(

        rmu.summary()

    )
