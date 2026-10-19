# -*- coding: utf-8 -*-
from beams_ec2 import BeamsEC2App


def main():
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == '--smoke-test':
        from beams_ec2.smoke_test import run_smoke_test
        raise SystemExit(run_smoke_test(sys.argv[2]))
    app = BeamsEC2App()
    app.mainloop()


if __name__ == "__main__":
    main()
