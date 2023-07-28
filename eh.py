





# target = self.engine.player
        # dx = target.x - self.parent.x
        # dy = target.y - self.parent.y
        # distance = max(abs(dx), abs(dy))  # Chebyshev distance.
        #
        # if self.engine.game_map.visible[self.parent.x, self.parent.y]:
        #     if distance <= 1:
        #         return MeleeAction(self.parent, dx, dy).perform()
        #
        #     self.path = self.get_path_to(target.x, target.y)
        #
        # if self.path:
        #     dest_x, dest_y = self.path.pop(0)
        #     return MovementAction(
        #         self.parent, dest_x - self.parent.x, dest_y - self.parent.y,
        #     ).perform()
        #
        # return WaitAction(self.parent).perform()