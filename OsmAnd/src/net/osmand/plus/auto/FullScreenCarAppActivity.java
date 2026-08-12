package net.osmand.plus.auto;

import android.os.Bundle;

import androidx.car.app.SessionInfo;
import androidx.car.app.activity.BaseCarAppActivity;

/**
 * Full-screen Automotive entry point with the same renderer initialization as CarAppActivity.
 *
 * <p>This is a real car-app activity rather than a transparent launcher that starts a second
 * CarAppActivity task. Keeping the declared launcher as the surface-owning activity lets the
 * Automotive task transition resize and preserve it like any other full-screen maps activity.
 */
public final class FullScreenCarAppActivity extends BaseCarAppActivity {

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);

		String sessionId = getIntent().getIdentifier();
		if (sessionId == null) {
			sessionId = String.valueOf(System.identityHashCode(this));
		}
		bindToViewModel(new SessionInfo(/* displayType= */ 0, sessionId));
	}
}
