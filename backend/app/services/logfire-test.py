import argparse
import logfire
from datetime import date


def run_logfire_test(dob: date, raise_error: bool) -> None:
    logfire.configure()
    logfire.info("Hello, {name}!", name="world")

    with logfire.span("Calculating age for {question}", question="dob"):
        logfire.debug("{dob=} {age=!r}", dob=dob, age=date.today() - dob)

    if raise_error:
        try:
            1 / 0
        except ZeroDivisionError:
            logfire.exception("Intentional exception for Logfire validation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Logfire integration smoke test")
    parser.add_argument(
        "--dob",
        help="Date of birth in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--no-input",
        action="store_true",
        help="Skip prompt and use a default date of birth",
    )
    parser.add_argument(
        "--raise-error",
        action="store_true",
        help="Emit a test exception event",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.dob:
        dob = date.fromisoformat(args.dob)
    elif args.no_input:
        dob = date(2000, 1, 1)
    else:
        user_input = input("How old are you [YYYY-mm-dd]? ")
        dob = date.fromisoformat(user_input)

    run_logfire_test(dob=dob, raise_error=args.raise_error)


if __name__ == "__main__":
    main()
