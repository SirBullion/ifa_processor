from runtime.runtime import runtime


class RelationService:

    def execute(self, parse_object):

        return runtime.execute(parse_object)


relation_service = RelationService()
