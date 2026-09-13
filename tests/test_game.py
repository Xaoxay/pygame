import copy
import unittest
from game import Game, LEVELS


class GameTests(unittest.TestCase):
    def setUp(self):
        self.g = Game(seed=7)
        self.g.new_game()

    def test_all_levels_fit_playfield_and_are_distinct(self):
        patterns = set()
        for i, (_, rows) in enumerate(LEVELS):
            patterns.add(tuple(rows))
            self.g.level = i
            self.g.load_level()
            self.assertTrue(self.g.bricks)
            for b in self.g.bricks:
                self.assertGreaterEqual(b['x'], 14)
                self.assertLessEqual(b['x'] + b['w'], 386)
                self.assertGreater(b['y'], 200)
                self.assertLess(b['y'] + b['h'], self.g.ceiling)
        self.assertEqual(len(patterns), 20)

    def test_losing_last_ball_costs_exactly_one_life(self):
        self.g.launch()
        self.g.balls[0]['y'] = 0
        self.g.tick(.1)
        self.assertEqual((self.g.lives, self.g.state), (2, 'ready'))
        self.g.tick(1)
        self.assertEqual(self.g.lives, 2)

    def test_multiball_loss_does_not_cost_life_until_all_lost(self):
        self.g.launch()
        self.g.balls.append(dict(self.g.balls[0], y=400))
        self.g.balls[0]['y'] = 0
        self.g.tick(.02)
        self.assertEqual((self.g.lives, len(self.g.balls)), (3, 1))

    def test_pause_freezes_game_and_resume_restores_it(self):
        self.g.launch()
        self.g.pause()
        before = copy.deepcopy(self.g.balls)
        self.g.tick(5)
        self.assertEqual(before, self.g.balls)
        self.g.resume()
        self.g.tick(.02)
        self.assertNotEqual(before, self.g.balls)

    def test_campaign_ends_after_twenty_levels_and_preserves_score(self):
        for level in range(20):
            self.assertEqual(self.g.level, level)
            self.g.launch()
            self.g.bricks.clear()
            self.g.tick(.02)
            expected = 'won' if level == 19 else 'clear'
            self.assertEqual(self.g.state, expected)
            score = self.g.score
            self.g.tick(.1)
            self.assertEqual(self.g.score, score)
            self.g.advance()
        self.assertEqual(self.g.score, 105000)
        self.g.new_game()
        self.assertEqual((self.g.level, self.g.score, self.g.lives), (0, 0, 3))

    def test_hard_brick_requires_multiple_contacts(self):
        self.g.launch()
        brick = dict(x=150, y=400, w=46, h=23, hp=3, row=0)
        self.g.bricks = [brick]
        for remaining in (2, 1, 0):
            self.g.balls = [dict(x=170, y=390, vx=0, vy=400, trail=[])]
            self.g.tick(.04)
            self.assertEqual(brick['hp'], remaining)
        self.assertEqual(self.g.state, 'clear')

    def test_wide_powerup_expires_and_paddle_stays_in_bounds(self):
        self.g.launch()
        self.g.drops = [dict(x=200, y=120, kind='wide')]
        self.g.tick(.01)
        self.assertEqual(self.g.paddle_width, 128)
        self.g.move_paddle(-1000)
        self.assertEqual(self.g.paddle[0], 14)
        self.g.wide_time = .001
        self.g.tick(.01)
        self.assertEqual(self.g.paddle_width, 100)

    def test_multiball_is_capped(self):
        self.g.launch()
        self.g.drops = [dict(x=200, y=120, kind='multi') for _ in range(8)]
        self.g.tick(.01)
        self.assertEqual(len(self.g.balls), 5)

    def test_fast_ball_bounces_instead_of_tunnelling(self):
        self.g.launch()
        self.g.bricks = [dict(x=150, y=400, w=46, h=23, hp=2, row=0)]
        self.g.balls = [dict(x=170, y=380, vx=0, vy=440, trail=[])]
        self.g.tick(.1)
        self.assertEqual(self.g.bricks[0]['hp'], 1)
        self.assertLess(self.g.balls[0]['vy'], 0)

    def test_final_life_ends_game(self):
        self.g.lives = 1
        self.g.launch()
        self.g.balls[0]['y'] = 0
        self.g.tick(.02)
        self.assertEqual(self.g.state, 'over')

    def test_rate_scales_motion_without_changing_direction(self):
        for rate in (1, 2, 3):
            self.g.new_game()
            self.g.set_rate(rate)
            self.g.launch()
            ball = self.g.balls[0]
            start, velocity = ball['y'], ball['vy']
            self.g.tick(.02)
            self.assertAlmostEqual(ball['y'] - start, velocity * .02 * rate)

    def test_x3_collision_flashes_and_does_not_tunnel(self):
        self.g.set_rate(3)
        self.g.launch()
        self.g.bricks = [dict(x=150, y=400, w=46, h=23, hp=2, row=0)]
        self.g.balls = [dict(x=170, y=380, vx=0, vy=440, trail=[])]
        self.g.tick(.1)
        self.assertEqual(self.g.bricks[0]['hp'], 1)
        self.assertLess(self.g.balls[0]['vy'], 0)
        self.assertGreater(self.g.balls[0]['flash'], 0)

    def test_wall_and_paddle_flash_and_decay(self):
        self.g.launch()
        ball = self.g.balls[0]
        ball.update(x=379, y=300, vx=260, vy=0)
        self.g.tick(.02)
        self.assertGreater(ball['flash'], 0)
        for _ in range(3):
            self.g.tick(.1)
        self.assertEqual(ball['flash'], 0)
        ball.update(x=200, y=134, vx=0, vy=-260)
        self.g.tick(.02)
        self.assertGreater(ball['flash'], 0)
        self.assertGreater(ball['vy'], 0)

    def test_speed_choice_survives_new_game(self):
        self.g.set_rate(3)
        self.g.new_game()
        self.assertEqual(self.g.rate, 3)
        with self.assertRaises(ValueError):
            self.g.set_rate(0)


if __name__ == '__main__':
    unittest.main()
