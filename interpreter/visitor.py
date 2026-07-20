class NodeVisitor:

    def visit(self, node):

        method = "visit_" + node.__class__.__name__

        visitor = getattr(self, method, self.generic_visit)

        return visitor(node)

    # ---------------------------------------

    def generic_visit(self, node):

        raise NotImplementedError(
            f"No visitor for {node.__class__.__name__}"
        )
