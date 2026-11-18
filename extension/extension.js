import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';

const APP_ID = 'io.github.aransiya.Scratchpad';

export default class ScratchpadExtension extends Extension {
    enable() {
        this._timer = 0;
        const installedId = this.dir.get_child('application-id');
        this._appId = APP_ID;
        if (installedId.query_exists(null)) {
            const [, contents] = installedId.load_contents(null);
            this._appId = new TextDecoder().decode(contents).trim();
        }
        this._indicator = new PanelMenu.Button(0, this.metadata.name, true);
        const button = new St.Button({
            accessible_name: 'Open 3aransiya',
            child: new St.Icon({
                gicon: new Gio.FileIcon({file: this.dir.get_child('3aransiya-symbolic.svg')}),
                style_class: 'system-status-icon',
            }),
        });
        button.connect('clicked', () => this._open());
        this._indicator.add_child(button);
        Main.panel.addToStatusArea(this.uuid, this._indicator);
    }

    disable() {
        if (this._timer)
            GLib.Source.remove(this._timer);
        this._timer = 0;
        this._indicator.destroy();
        this._indicator = null;
    }

    _findWindow() {
        return global.get_window_actors()
            .map(actor => actor.meta_window)
            .find(window => window.get_gtk_application_id() === this._appId);
    }

    _focus(window) {
        const workspace = global.workspace_manager.get_active_workspace();
        if (!window.is_on_all_workspaces() && window.get_workspace() !== workspace)
            window.change_workspace(workspace);
        Main.activateWindow(window);
    }

    _open() {
        if (this._timer)
            return;
        const existing = this._findWindow();
        if (existing) {
            this._focus(existing);
            return;
        }

        const monitor = global.display.get_current_monitor();
        try {
            Gio.Subprocess.new(
                [this.dir.get_child('launch-scratchpad').get_path()],
                Gio.SubprocessFlags.NONE
            );
        } catch (error) {
            Main.notify('3aransiya', 'Could not launch the scratchpad. Check its installation.');
            logError(error);
            return;
        }

        const deadline = GLib.get_monotonic_time() + 5 * GLib.USEC_PER_SEC;
        this._timer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 75, () => {
            const window = this._findWindow();
            if (window && window.get_frame_rect().width > 1) {
                this._focus(window);
                const workArea = window.get_work_area_for_monitor(monitor);
                if (workArea) {
                    const {width, height} = window.get_frame_rect();
                    const x = workArea.x + Math.max(0, Math.floor((workArea.width - width) / 2));
                    const y = workArea.y + Math.max(0, workArea.height - height - 24);
                    window.move_frame(false, x, y);
                }
            } else if (GLib.get_monotonic_time() < deadline) {
                return GLib.SOURCE_CONTINUE;
            } else {
                Main.notify('3aransiya', 'The scratchpad window did not appear.');
            }
            this._timer = 0;
            return GLib.SOURCE_REMOVE;
        });
    }
}
