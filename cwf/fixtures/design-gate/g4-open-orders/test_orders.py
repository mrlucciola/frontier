import unittest

import orders


class OrdersTest(unittest.TestCase):
    def test_orders_with_status(self):
        self.assertEqual([o["id"] for o in orders.orders_with_status("shipped")], [2])


if __name__ == "__main__":
    unittest.main()
