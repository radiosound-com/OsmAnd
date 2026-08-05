package net.osmand.plus.auto;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;

import androidx.car.app.activity.CarAppActivity;

/** Launches the stock CarAppActivity into a fresh full-screen task. */
public final class FullScreenCarAppActivity extends Activity {

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);

		ActivityManager activityManager = getSystemService(ActivityManager.class);
		for (ActivityManager.AppTask appTask : activityManager.getAppTasks()) {
			ActivityManager.RecentTaskInfo taskInfo = appTask.getTaskInfo();
			if (taskInfo.id == getTaskId() || !isCarAppTask(taskInfo)) {
				continue;
			}
			appTask.finishAndRemoveTask();
		}

		Intent intent = new Intent(this, CarAppActivity.class);
		intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
		startActivity(intent);
		finish();
	}

	private static boolean isCarAppTask(ActivityManager.RecentTaskInfo taskInfo) {
		return isCarAppActivity(taskInfo.baseActivity) || isCarAppActivity(taskInfo.topActivity);
	}

	private static boolean isCarAppActivity(ComponentName componentName) {
		return componentName != null
				&& CarAppActivity.class.getName().equals(componentName.getClassName());
	}
}
