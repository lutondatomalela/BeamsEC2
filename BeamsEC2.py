# -*- coding: utf-8 -*-
import argparse


def main():
    parser = argparse.ArgumentParser(description='BeamsEC2')
    parser.add_argument('--smoke-test', metavar='OUTPUT_DIRECTORY',
                        help='Run the packaged GUI calculation/export check and exit')
    args = parser.parse_args()
    if args.smoke_test:
        from beams_ec2.smoke_test import run_smoke_test
        return run_smoke_test(args.smoke_test)
    from beams_ec2 import BeamsEC2App
    app = BeamsEC2App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
