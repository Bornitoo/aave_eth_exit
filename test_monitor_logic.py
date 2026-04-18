"""
Unit tests for monitor open/close alert logic.
Simulates the was_open state machine with various thresholds and free values.
"""
from decimal import Decimal

def simulate(events: list[tuple], threshold: Decimal) -> list[str]:
    """
    events: list of (free_usd,) values over time
    Returns list of alerts fired.
    """
    was_open = False
    alerts = []
    for (free,) in events:
        free = Decimal(str(free))
        is_open = free >= threshold
        if is_open and not was_open:
            alerts.append(f"OPEN  free={free} thr={threshold}")
        elif was_open and not is_open:
            alerts.append(f"CLOSE free={free} thr={threshold}")
        was_open = is_open
    return alerts


def run_tests():
    passed = 0
    failed = 0

    def check(name, got, expected):
        nonlocal passed, failed
        if got == expected:
            print(f"  ✅ {name}")
            passed += 1
        else:
            print(f"  ❌ {name}")
            print(f"     got:      {got}")
            print(f"     expected: {expected}")
            failed += 1

    print("\n── Threshold=$1000 ─────────────────────────────────────────")

    # 1. Stays below threshold — no alerts
    check("no alert when always below",
        simulate([(500,), (300,), (900,)], Decimal("1000")),
        [])

    # 2. Crosses above — open alert fires once
    check("open fires once on rise",
        simulate([(500,), (1000,), (1500,), (2000,)], Decimal("1000")),
        ["OPEN  free=1000 thr=1000"])

    # 3. Crosses above then drops — open then close
    check("open then close",
        simulate([(500,), (1500,), (800,)], Decimal("1000")),
        ["OPEN  free=1500 thr=1000", "CLOSE free=800 thr=1000"])

    # 4. Oscillates around threshold — alternating alerts
    check("oscillates — alternating open/close",
        simulate([(500,), (1500,), (500,), (1500,)], Decimal("1000")),
        ["OPEN  free=1500 thr=1000", "CLOSE free=500 thr=1000",
         "OPEN  free=1500 thr=1000"])

    # 5. Starts above threshold — open fires on first tick
    check("starts above — open on first tick",
        simulate([(2000,), (2000,)], Decimal("1000")),
        ["OPEN  free=2000 thr=1000"])

    # 6. Exactly at threshold — counts as open
    check("exactly at threshold = open",
        simulate([(999,), (1000,)], Decimal("1000")),
        ["OPEN  free=1000 thr=1000"])

    print("\n── Threshold=$3 (user's actual case) ───────────────────────")

    # 7. free=4 with threshold=3 → should open, NOT close
    check("free=4, thr=3 → open (not close)",
        simulate([(0,), (4,)], Decimal("3")),
        ["OPEN  free=4 thr=3"])

    # 8. free drops from 4 to 2 → close
    check("free=4→2, thr=3 → open then close",
        simulate([(4,), (2,)], Decimal("3")),
        ["OPEN  free=4 thr=3", "CLOSE free=2 thr=3"])

    # 9. No spurious $100 threshold anywhere
    check("close uses user thr=$3, not $100",
        simulate([(0,), (5,), (2,)], Decimal("3")),
        ["OPEN  free=5 thr=3", "CLOSE free=2 thr=3"])

    print("\n── No duplicate alerts ──────────────────────────────────────")

    # 10. Stays above — only one open, no repeats
    check("stays above — open fires only once",
        simulate([(1500,), (2000,), (3000,)], Decimal("1000")),
        ["OPEN  free=1500 thr=1000"])

    # 11. Stays below after close — no second close
    check("stays below — close fires only once",
        simulate([(2000,), (500,), (300,), (100,)], Decimal("1000")),
        ["OPEN  free=2000 thr=1000", "CLOSE free=500 thr=1000"])

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    ok = run_tests()
    exit(0 if ok else 1)
