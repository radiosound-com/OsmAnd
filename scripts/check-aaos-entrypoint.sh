#!/bin/sh

set -eu

ADB=${ADB:-adb}
PACKAGE=${PACKAGE:-net.osmand.dev}
COMPONENT="$PACKAGE/androidx.car.app.activity.CarAppActivity"

resolved=$(
	"$ADB" shell cmd package resolve-activity --brief \
		-a android.intent.action.MAIN \
		-c android.intent.category.APP_MAPS \
	| tail -n 1 | tr -d '\r'
)

if [ "$resolved" != "$COMPONENT" ]; then
	echo "FAIL: APP_MAPS resolves to $resolved (expected $COMPONENT)" >&2
	exit 1
fi

host_count=$(
	"$ADB" shell pm list packages \
		| tr -d '\r' \
		| grep -E -c '^package:com\.android\.car\.libraries\.templates\.host$' || true
)
stock_host_count=$(
	"$ADB" shell pm list packages \
		| tr -d '\r' \
		| grep -E -c '^package:com\.android\.car\.templates\.host$' || true
)
if [ "$host_count" -ne 1 ] || [ "$stock_host_count" -ne 0 ]; then
	echo "FAIL: expected only Caramel's templates host (custom=$host_count stock=$stock_host_count)" >&2
	exit 1
fi

"$ADB" shell am force-stop "$PACKAGE"
"$ADB" shell am start -W -n "$COMPONENT" >/dev/null
sleep 2

top=$(
	"$ADB" shell dumpsys activity activities \
	| grep 'topResumedActivity=' \
	| grep "$PACKAGE" \
	| head -n 1 | tr -d '\r' || true
)
case "$top" in
	*"$COMPONENT"*) ;;
	*) echo "FAIL: top activity is not $COMPONENT: $top" >&2; exit 1 ;;
esac

bindings=$(
	"$ADB" shell dumpsys activity services "$PACKAGE" \
		| grep -E -c 'templates\.host|TemplatesHostService|renderer_service' || true
)
if [ "$bindings" -eq 0 ]; then
	echo "FAIL: CarAppService is not bound to an Automotive templates host" >&2
	exit 1
fi

echo "PASS: $COMPONENT rendered through an Automotive templates host"
