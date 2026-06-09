from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import time
import random

camera_off_on = True

FIRST_PERSON = False
Door_angle = 0.0
Door_open = False
DOOR_SPEED = 2.0
blue_key_active = True
green_key_active = True
cyan_key_active = True
purple_key_active = True
has_blue_key = False
has_purple_key = False
has_cyan_key = False
has_green_key = False
blue_key_box = [-16, 21.5, 6, 6]
purple_key_box = [3.1, 23, 6, 6]
cyan_key_box = [16, 22, 6, 6]
green_key_box = [32, -20, 6, 6]
key_buffer = 1.5
Door_blue_open = False
Door_purple_open = False
Door_cyan_open = False
Door_green_open = False
Door_blue_angle = 0.0
Door_purple_angle = 0.0
Door_cyan_angle = 0.0
Door_green_angle = 0.0
DOOR_SPEED = 2.0
Door_open = False
Door_angle = 0.0
Grid_rows = 20
Grid_cols = 30
Floortile_size = 2.5
Floor_width = (Grid_cols // 2) * Floortile_size
Floor_length = (Grid_rows // 2) * Floortile_size
GAME_OVER = False
MISSION_SUCCESS = False
MISSION_FAILED = False
CATCH_DIST = 1.6
TREASURE_TAKEN = False
TREASURE_PICK_RADIUS = 2.2
TREASURE_X = -Floor_width + 5.0
TREASURE_Z = -Floor_length + 1.0
EXIT_Z_THRESHOLD = -Floor_length - 2.0
EVER_DETECTED = False
thief_x = 0
thief_z = -35
thief_dir_angle = 0.0
thief_leg_anim = 0.0
thief_buffer = 0.8
WALK_STEP = 0.7
RUN_MULT = 1.8
key_down = {b'w': False, b's': False, b'a': False, b'd': False}
run_down = False  # True while 'f' is held
special_down = {GLUT_KEY_UP: False, GLUT_KEY_DOWN: False, GLUT_KEY_LEFT: False, GLUT_KEY_RIGHT: False}


def clear_movement_inputs():
    for k in key_down:
        key_down[k] = False
    for k in special_down:
        special_down[k] = False


last_anim_time = 0.0
furniture_boxes = [
    [0, 0, 7.0, 7.0],
    [24, -10, 11, 12],
    [-30, -13.5, 5, 7.5],
    [-30.5, 8, 11.5, 6.5],
    [24.5, 13, 11.5, 7.5],
    [35.5, 8, 3, 8],
    [0, 26, 100, 1],
    [20, -26, 33, 1],
    [-20, -26, 33, 1],
    [-39, 0, 1, 60],
    [39, 0, 1, 60],
    [13, 0, 1, 20],
    [-13, 0, 1, 20],
    [13, -20, 1, 10],
    [-13, -20, 1, 10],
    [13, 20, 1, 10],
    [-13, 20, 1, 10],
    [3.1, 23, 4.5, 4.5],
    [-16, 21.5, 4.5, 4.5],
    [16, 22, 4.5, 4.5],
    [32, -20, 4.5, 4.5]
]
CHEAT_MODE = False
CHEAT_NOCLIP = True
CHEAT_INVISIBLE = True
CHEAT_ALL_KEYS = True
CHEAT_GODMODE = True


def dist2(ax, az, bx, bz):
    dx = ax - bx
    dz = az - bz
    return dx * dx + dz * dz


def guard_sensor_facing_deg(render_angle_deg):
    return clamp_angle_deg(render_angle_deg)


def clamp_angle_deg(a):
    a %= 360.0
    if a < 0: a += 360.0
    return a


def angle_to_target_deg(ax, az, bx, bz):
    dx = bx - ax
    dz = bz - az
    return clamp_angle_deg(math.degrees(math.atan2(dx, dz)))  # 0 = +Z


def angle_diff_deg(a, b):
    return (b - a + 180.0) % 360.0 - 180.0


def point_in_fov(ox, oz, o_angle, tx, tz, max_dist, fov_half_deg):
    if dist2(ox, oz, tx, tz) > max_dist * max_dist:
        return False
    desired = angle_to_target_deg(ox, oz, tx, tz)
    return abs(angle_diff_deg(o_angle, desired)) <= fov_half_deg


def point_in_rect(px, pz, cx, cz, w, d):
    return (cx - w / 2 <= px <= cx + w / 2) and (cz - d / 2 <= pz <= cz + d / 2)


def line_blocked_by_rect(ax, az, bx, bz, cx, cz, w, d, step=0.5):
    dist = math.hypot(bx - ax, bz - az)
    if dist < 1e-6:
        return False
    steps = max(1, int(dist / step))
    for i in range(steps + 1):
        t = i / steps
        px = ax + (bx - ax) * t
        pz = az + (bz - az) * t
        if point_in_rect(px, pz, cx, cz, w, d):
            return True
    return False


def has_line_of_sight(ax, az, bx, bz):
    blockers = []
    for item in furniture_boxes:
        cx, cz, w, d = item
        if (w <= 1.5 and d >= 10) or (d <= 1.5 and w >= 10):
            blockers.append((cx, cz, w, d))
    if not Door_open:
        blockers.append((0.0, door_z_center, Door_width, wall_thickness))
    door_w, door_h, door_t = 4.0, 4.1, 1.2
    z_back, z_front = Floor_length / 2.0, -Floor_length / 2.0
    part_width = (2 * Floor_width) / 3.0
    x1 = -Floor_width + part_width
    x2 = -Floor_width + 2 * part_width
    if not Door_blue_open:
        blockers.append((x1, z_back, door_t, door_w))
    if not Door_green_open:
        blockers.append((x1, z_front, door_t, door_w))
    if not Door_cyan_open:
        blockers.append((x2, z_back, door_t, door_w))
    if not Door_purple_open:
        blockers.append((x2, z_front, door_t, door_w))
    for (cx, cz, w, d) in blockers:
        if line_blocked_by_rect(ax, az, bx, bz, cx, cz, w, d):
            return False
    return True


def draw_detection_rays(origin_x, origin_y, origin_z, facing_angle_deg, fov_deg, max_dist, color_rgb, ray_count=35):
    glColor3f(*color_rgb)
    glBegin(GL_LINES)
    start_ang = facing_angle_deg - fov_deg
    end_ang = facing_angle_deg + fov_deg
    for i in range(ray_count):
        t = i / (ray_count - 1) if ray_count > 1 else 0
        ang = math.radians(start_ang + (end_ang - start_ang) * t)
        dx = math.sin(ang)
        dz = math.cos(ang)
        px = origin_x + dx * max_dist
        pz = origin_z + dz * max_dist
        glVertex3f(origin_x, origin_y, origin_z)
        glVertex3f(px, origin_y, pz)
    glEnd()


def draw_billboard_symbol(x, y, z, text, color, scale=0.012, line_w=3.5, depth_test=True):
    glPushAttrib(GL_ENABLE_BIT | GL_LINE_BIT | GL_CURRENT_BIT)
    if not depth_test:
        glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glLineWidth(line_w)
    glColor3f(*color)
    glPushMatrix()
    glTranslatef(x, y, z)
    mv = glGetDoublev(GL_MODELVIEW_MATRIX)
    mv[0][0] = 1;
    mv[0][1] = 0;
    mv[0][2] = 0
    mv[1][0] = 0;
    mv[1][1] = 1;
    mv[1][2] = 0
    mv[2][0] = 0;
    mv[2][1] = 0;
    mv[2][2] = 1
    glLoadMatrixd(mv)
    glScalef(scale, scale, scale)
    glTranslatef(-50, 0, 0)
    for ch in text:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(ch))
    glPopMatrix()
    glPopAttrib()


def trigger_alert(source):
    global ALERTED, ALERT_SOURCE, last_seen_time
    global guard_symbol_timer, cctv_symbol_timer, player_spotted_timer
    global EVER_DETECTED
    EVER_DETECTED = True
    now = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    if not ALERTED:
        player_spotted_timer = SPOTTED_SYMBOL_DURATION
    if source == "GUARD":
        guard_symbol_timer = GUARD_SYMBOL_DURATION
    elif source == "CCTV":
        cctv_symbol_timer = CCTV_SYMBOL_DURATION
    ALERTED = True
    ALERT_SOURCE = source
    last_seen_time = now


def init_hide_spots():
    global hide_spots
    part_width = (2 * Floor_width) / 3
    x1 = -Floor_width + part_width
    x2 = -Floor_width + 2 * part_width
    wall_x = 13.0
    wall_thickness_local = 1.0
    box_width = 2.4
    gap = 0.15
    guard_hide_x = wall_x - (wall_thickness_local / 2.0) - (box_width / 2.0) - gap
    guard_hide_z = 0.0
    hide_spots = [
        (-Floor_width + 15.0, Floor_length - 2.0),
        (guard_hide_x, guard_hide_z),
        (x2 - 21.0, -Floor_length + 20.0),
        (x2 + 8.0, Floor_length - 22.0),
        (Floor_width - 20.0, -Floor_length + 22.0),
    ]


def try_auto_hide():
    global is_hidden, hidden_spot_index, thief_leg_anim
    if is_hidden or ALERTED:
        return
    for i, (hx, hz) in enumerate(hide_spots):
        if dist2(thief_x, thief_z, hx, hz) <= (HIDE_ENTER_RADIUS * HIDE_ENTER_RADIUS):
            is_hidden = True
            hidden_spot_index = i
            thief_leg_anim = 0.0
            clear_movement_inputs()
            print("HIDDEN")
            return


def exit_hide():
    global is_hidden, hidden_spot_index, thief_x, thief_z
    if not is_hidden:
        return
    hx, hz = hide_spots[hidden_spot_index]
    rad = math.radians(thief_dir_angle)
    fx = math.sin(rad)
    fz = math.cos(rad)
    candidates = [
        (hx + fx * HIDE_EXIT_PUSH, hz + fz * HIDE_EXIT_PUSH),
        (hx - fx * HIDE_EXIT_PUSH, hz - fz * HIDE_EXIT_PUSH),
        (hx + fz * HIDE_EXIT_PUSH, hz - fx * HIDE_EXIT_PUSH),
        (hx - fz * HIDE_EXIT_PUSH, hz + fx * HIDE_EXIT_PUSH),
    ]
    for nx, nz in candidates:
        if not check_collision(nx, nz):
            thief_x, thief_z = nx, nz
            break
    else:
        thief_x, thief_z = hx, hz
    is_hidden = False
    hidden_spot_index = -1
    print("EXITED HIDING")


def init_guard():
    global guard_x, guard_z, guard_dir_angle
    guard_x = 0.0
    guard_z = -Floor_length / 2 + 5.0
    guard_dir_angle = 180.0


def guard_detection_update():
    global CHEAT_MODE, CHEAT_INVISIBLE
    if CHEAT_MODE and CHEAT_INVISIBLE:
        return
    if is_hidden:
        return
    guard_facing = clamp_angle_deg(guard_dir_angle)
    rad = math.radians(guard_facing)
    fx = math.sin(rad)
    fz = math.cos(rad)
    eye_forward = 0.8
    eye_x = guard_x + fx * eye_forward
    eye_z = guard_z + fz * eye_forward
    if point_in_fov(eye_x, eye_z, guard_facing, thief_x, thief_z, GUARD_VIEW_DIST, GUARD_VIEW_FOV):
        if has_line_of_sight(eye_x, eye_z, thief_x, thief_z):
            trigger_alert("GUARD")


def guard_ai_update(dt):
    global guard_state, guard_patrol_i, guard_dir_angle, guard_x, guard_z
    global cctv_has_target, cctv_last_detect_x, cctv_last_detect_z
    global guard_walk_phase
    obstacles = build_guard_obstacles()
    if ALERTED:
        if ALERT_SOURCE == "GUARD":
            guard_state = GUARD_STATE_CHASE
        elif ALERT_SOURCE == "CCTV" and cctv_has_target:
            guard_state = GUARD_STATE_INVESTIGATE
        else:
            guard_state = GUARD_STATE_PATROL
    else:
        guard_state = GUARD_STATE_PATROL
    if guard_state == GUARD_STATE_CHASE:
        desired = angle_to_target_deg(guard_x, guard_z, thief_x, thief_z)
        guard_dir_angle = desired
        rad = math.radians(guard_dir_angle)
        nx = guard_x + math.sin(rad) * GUARD_CHASE_SPEED * dt
        nz = guard_z + math.cos(rad) * GUARD_CHASE_SPEED * dt
        ok, gx, gz = guard_step_move(
            guard_x, guard_z,
            math.sin(rad) * GUARD_CHASE_SPEED,
            math.cos(rad) * GUARD_CHASE_SPEED,
            dt, obstacles,
            max_step=0.30
        )
        if ok:
            moved = math.hypot(gx - guard_x, gz - guard_z)
            guard_x, guard_z = gx, gz
            if moved > 1e-6:
                guard_walk_phase += moved * GUARD_STEP_FREQ
        else:
            guard_dir_angle = clamp_angle_deg(guard_dir_angle + random.uniform(-140, 140) * dt)
        return
    if guard_state == GUARD_STATE_INVESTIGATE:
        tx, tz = cctv_last_detect_x, cctv_last_detect_z
        desired = angle_to_target_deg(guard_x, guard_z, tx, tz)
        diff = angle_diff_deg(guard_dir_angle, desired)
        max_turn = GUARD_INVEST_TURN_SPEED * dt
        diff = max(min(diff, max_turn), -max_turn)
        guard_dir_angle = clamp_angle_deg(guard_dir_angle + diff)
        rad = math.radians(guard_dir_angle)
        nx = guard_x + math.sin(rad) * GUARD_INVESTIGATE_SPEED * dt
        nz = guard_z + math.cos(rad) * GUARD_INVESTIGATE_SPEED * dt
        ok, gx, gz = guard_step_move(
            guard_x, guard_z,
            math.sin(rad) * GUARD_INVESTIGATE_SPEED,
            math.cos(rad) * GUARD_INVESTIGATE_SPEED,
            dt, obstacles,
            max_step=0.35
        )
        if ok:
            moved = math.hypot(gx - guard_x, gz - guard_z)
            guard_x, guard_z = gx, gz
            if moved > 1e-6:
                guard_walk_phase += moved * GUARD_STEP_FREQ
        else:
            guard_dir_angle = clamp_angle_deg(guard_dir_angle + random.uniform(-120, 120) * dt)
        if dist2(guard_x, guard_z, tx, tz) <= (INVESTIGATE_REACH_DIST * INVESTIGATE_REACH_DIST):
            guard_dir_angle = clamp_angle_deg(guard_dir_angle + 120.0 * dt)
        return
    tx, tz = guard_patrol_points[guard_patrol_i]
    desired = angle_to_target_deg(guard_x, guard_z, tx, tz)
    diff = angle_diff_deg(guard_dir_angle, desired)
    max_turn = GUARD_PATROL_TURN_SPEED * dt
    diff = max(min(diff, max_turn), -max_turn)
    guard_dir_angle = clamp_angle_deg(guard_dir_angle + diff)
    rad = math.radians(guard_dir_angle)
    nx = guard_x + math.sin(rad) * GUARD_PATROL_SPEED * dt
    nz = guard_z + math.cos(rad) * GUARD_PATROL_SPEED * dt
    ok, gx, gz = guard_step_move(
        guard_x, guard_z,
        math.sin(rad) * GUARD_PATROL_SPEED,
        math.cos(rad) * GUARD_PATROL_SPEED,
        dt, obstacles,
        max_step=0.35
    )
    if ok:
        moved = math.hypot(gx - guard_x, gz - guard_z)
        guard_x, guard_z = gx, gz
        if moved > 1e-6:
            guard_walk_phase += moved * GUARD_STEP_FREQ
    else:
        guard_dir_angle = clamp_angle_deg(guard_dir_angle + random.uniform(-90, 90) * dt)
    if ok and dist2(guard_x, guard_z, tx, tz) < 1.0:
        guard_patrol_i = (guard_patrol_i + 1) % len(guard_patrol_points)


def try_press_power_button():
    global CCTV_POWER_ON
    global ALERTED, ALERT_SOURCE, last_seen_time
    global guard_symbol_timer, cctv_symbol_timer, player_spotted_timer
    global alert_symbol_timer, high_alert_timer
    global cctv_has_target
    if dist2(thief_x, thief_z, POWER_BUTTON_X, POWER_BUTTON_Z) <= (POWER_BUTTON_RADIUS * POWER_BUTTON_RADIUS):
        CCTV_POWER_ON = not CCTV_POWER_ON
        if not CCTV_POWER_ON:
            cctv_has_target = False
            ALERTED = False
            ALERT_SOURCE = ""
            last_seen_time = -9999.0
            guard_symbol_timer = 0.0
            cctv_symbol_timer = 0.0
            player_spotted_timer = 0.0
            alert_symbol_timer = 0.0
            high_alert_timer = 0.0
        print("CCTV POWER:", "ON" if CCTV_POWER_ON else "OFF")


def handle_keys(key, x, y):
    global thief_x, thief_z, thief_dir_angle, thief_leg_anim
    global GAME_OVER, MISSION_SUCCESS, MISSION_FAILED
    global TREASURE_TAKEN
    global FIRST_PERSON
    global Door_open
    global is_hidden
    global has_blue_key, has_green_key, has_cyan_key, has_purple_key
    global blue_key_active, green_key_active, cyan_key_active, purple_key_active
    global run_down
    global CHEAT_MODE, CHEAT_NOCLIP, CHEAT_INVISIBLE, CHEAT_ALL_KEYS, CHEAT_GODMODE
    if key in (b'c', b'C'):
        CHEAT_MODE = not CHEAT_MODE
        print("CHEAT MODE:", "ON" if CHEAT_MODE else "OFF")
        glutPostRedisplay()
        return
    mods = glutGetModifiers()
    now = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    if GAME_OVER or MISSION_SUCCESS or MISSION_FAILED:
        if key in (b'r', b'R'):
            restart_game()
        return
    running = (mods & GLUT_ACTIVE_SHIFT) != 0
    step = WALK_STEP * (RUN_MULT if running else 1.0)
    turn_speed = 5.0
    if is_hidden:
        if key in key_down or key == b'f':
            return
        if key == b'h':
            exit_hide()
        elif key == b'v':
            FIRST_PERSON = not FIRST_PERSON
        glutPostRedisplay()
        return
        # Hold F to run
    if key == b'f':
        run_down = True
        return
    if key in key_down:
        key_down[key] = True
        return
    next_x = thief_x
    next_z = thief_z
    next_angle = thief_dir_angle
    rad = math.radians(thief_dir_angle)
    forward_x = math.sin(rad)
    forward_z = math.cos(rad)
    right_x = math.sin(rad + math.pi / 2)
    right_z = math.cos(rad + math.pi / 2)
    moved = False
    if key == b'w':
        next_x += forward_x * step
        next_z += forward_z * step
        moved = True
    elif key == b's':
        next_x -= forward_x * step
        next_z -= forward_z * step
        moved = True
    elif key == b'a':
        next_angle += turn_speed
    elif key == b'd':
        next_angle -= turn_speed
    elif key == b'q':
        next_angle += turn_speed
    elif key == b'e':
        next_angle -= turn_speed
    elif key == b'v':
        FIRST_PERSON = not FIRST_PERSON
        glutPostRedisplay()
        return
    elif key in (b'b', b'B'):
        try_press_power_button()
        glutPostRedisplay()
        return
    elif key == b'p':
        door_w, door_h, door_t = 4.0, 4.1, 1.2
        z_back, z_front = Floor_length / 2.0, -Floor_length / 2.0
        part_width = (2 * Floor_width) / 3.0
        x1 = -Floor_width + part_width
        x2 = -Floor_width + 2 * part_width

        def near(dx, dz, th=2.6):
            return dist2(thief_x, thief_z, dx, dz) <= th * th

        if near(x1, z_back):
            if has_blue_key:
                global Door_blue_open
                Door_blue_open = not Door_blue_open
            return

        if near(x1, z_front):
            if has_green_key:
                global Door_green_open
                Door_green_open = not Door_green_open
            return
        # detected
        if near(x2, z_back):
            if has_cyan_key:
                global Door_cyan_open
                Door_cyan_open = not Door_cyan_open
            return

        if near(x2, z_front):
            if has_purple_key:
                global Door_purple_open
                Door_purple_open = not Door_purple_open
            return

        Door_open = not Door_open
        glutPostRedisplay()
        return
    elif key == b'm':
        if -16 + 6 > thief_x > -16 - 6 and -22 - 8 < thief_z < -22 + 8:
            camera_off_on = False
            print("cctv off")
    elif key == b't':
        if -26 + 6 > thief_x > -26 - 6 and -22 - 8 < thief_z < -22 + 8:
            print("Treasure collected")
    elif key == b'k':
        # BLUE KEY
        if 32 - 8 < thief_x < 32 + 8 and -20 - 8 < thief_z < -20 + 8:
            if blue_key_active:
                bx, bz, bw, bd = blue_key_box
                has_blue_key = True
                blue_key_active = False
                print("Blue key picked!")

        # GREEN KEY
        if 16 + 12 > thief_x > 16 - 12 and 22 - 12 < thief_z < 22 + 12:
            if green_key_active:
                gx, gz, gw, gd = green_key_box
                has_green_key = True
                green_key_active = False
                print("Green key picked!")

        # CYAN KEY
        if -16 + 6 > thief_x > -16 - 6 and 22 - 8 < thief_z < 22 + 8:
            if cyan_key_active:
                cx, cz, cw, cd = cyan_key_box
                has_cyan_key = True
                cyan_key_active = False
                print("Cyan key picked!")

        # PURPLE KEY
        if 3.1 + 8 > thief_x > 3.1 - 8 and 23 - 8 < thief_z < 23 + 8:
            if purple_key_active:
                px, pz, pw, pd = purple_key_box
                has_purple_key = True
                purple_key_active = False
                print("Purple key picked!")

        glutPostRedisplay()
        return

    next_angle %= 360
    thief_dir_angle = next_angle
    if not check_collision(next_x, next_z):
        dx = next_x - thief_x
        dz = next_z - thief_z
        thief_x = next_x
        thief_z = next_z
        if moved:
            thief_leg_anim += 10 if running else 6
        try_auto_hide()
    glutPostRedisplay()


def handle_keys_up(key, x, y):
    global run_down
    if key in key_down:
        key_down[key] = False
    if key == b'f':
        run_down = False


def ArrowKeyUp(key, x, y):
    if key in special_down:
        special_down[key] = False


wall_thickness = 1
door_z_center = -Floor_length - wall_thickness / 2


def rect_collide(px, pz, cx, cz, w, d, buffer_radius):
    min_x = cx - w / 2 - buffer_radius
    max_x = cx + w / 2 + buffer_radius
    min_z = cz - d / 2 - buffer_radius
    max_z = cz + d / 2 + buffer_radius
    return (min_x <= px <= max_x) and (min_z <= pz <= max_z)


GUARD_RADIUS = 0.9


def build_guard_obstacles():
    obs = [(cx, cz, w, d) for (cx, cz, w, d) in furniture_boxes]
    if not Door_open:
        obs.append((0.0, door_z_center, Door_width, wall_thickness))
    door_w, door_h, door_t = 4.0, 4.1, 1.2
    z_back, z_front = Floor_length / 2.0, -Floor_length / 2.0
    part_width = (2 * Floor_width) / 3.0
    x1 = -Floor_width + part_width
    x2 = -Floor_width + 2 * part_width
    if not Door_blue_open:
        obs.append((x1, z_back, door_t, door_w))
    if not Door_green_open:
        obs.append((x1, z_front, door_t, door_w))
    if not Door_cyan_open:
        obs.append((x2, z_back, door_t, door_w))
    if not Door_purple_open:
        obs.append((x2, z_front, door_t, door_w))
    return obs


def guard_collides(px, pz, obstacles):
    for (cx, cz, w, d) in obstacles:
        if rect_collide(px, pz, cx, cz, w, d, GUARD_RADIUS):
            return True
    return False


def guard_move_with_slide(from_x, from_z, to_x, to_z, obstacles):
    if not guard_collides(to_x, to_z, obstacles):
        return True, to_x, to_z
    if not guard_collides(to_x, from_z, obstacles):
        return True, to_x, from_z
    if not guard_collides(from_x, to_z, obstacles):
        return True, from_x, to_z
    return False, from_x, from_z


def guard_step_move(from_x, from_z, vel_x, vel_z, dt, obstacles, max_step=0.35):
    dx = vel_x * dt
    dz = vel_z * dt
    dist = math.hypot(dx, dz)
    if dist < 1e-6:
        return True, from_x, from_z
    steps = max(1, int(math.ceil(dist / max_step)))
    x, z = from_x, from_z
    for _ in range(steps):
        nx = x + dx / steps
        nz = z + dz / steps
        ok, x2, z2 = guard_move_with_slide(x, z, nx, nz, obstacles)
        if not ok:
            return False, x, z
        x, z = x2, z2
    return True, x, z


def check_collision(px, pz):
    global CHEAT_MODE, CHEAT_NOCLIP
    if CHEAT_MODE and CHEAT_NOCLIP:
        return False
    for item in furniture_boxes:
        f_x = item[0]
        f_z = item[1]
        f_w = item[2]
        f_d = item[3]
        min_x = f_x - (f_w / 2) - thief_buffer
        max_x = f_x + (f_w / 2) + thief_buffer
        min_z = f_z - (f_d / 2) - thief_buffer
        max_z = f_z + (f_d / 2) + thief_buffer
        if min_x <= px <= max_x and min_z <= pz <= max_z:
            return True
    if not Door_blue_open:
        if (-Floor_width + 10 - thief_buffer <= px <= -Floor_width + 14 + thief_buffer) and \
                (-Floor_length + 0 - thief_buffer <= pz <= -Floor_length + 4 + thief_buffer):
            return True
    if not Door_purple_open and not has_purple_key:
        if (-Floor_width + 2 - thief_buffer <= px <= -Floor_width + 6 + thief_buffer) and \
                (-Floor_length + 0 - thief_buffer <= pz <= -Floor_length + 4 + thief_buffer):
            return True
    if not Door_cyan_open and not has_cyan_key:
        if (Floor_width - 14 - thief_buffer <= px <= Floor_width - 10 + thief_buffer) and \
                (-Floor_length + 0 - thief_buffer <= pz <= -Floor_length + 4 + thief_buffer):
            return True
    if not Door_green_open and not has_green_key:
        if (Floor_width - 6 - thief_buffer <= px <= Floor_width - 2 + thief_buffer) and \
                (-Floor_length + 0 - thief_buffer <= pz <= -Floor_length + 4 + thief_buffer):
            return True
    if not Door_open:
        door_min_x = -Door_width / 2 - thief_buffer
        door_max_x = Door_width / 2 + thief_buffer
        door_min_z = door_z_center - wall_thickness / 2 - thief_buffer
        door_max_z = door_z_center + wall_thickness / 2 + thief_buffer
        if door_min_x <= px <= door_max_x and door_min_z <= pz <= door_max_z:
            return True
    return False


def check_caught():
    global GAME_OVER
    global CHEAT_MODE, CHEAT_GODMODE
    if CHEAT_MODE and CHEAT_GODMODE:
        return
    if GAME_OVER or MISSION_SUCCESS or MISSION_FAILED:
        return
    if is_hidden:
        return
    if dist2(guard_x, guard_z, thief_x, thief_z) <= (CATCH_DIST * CATCH_DIST):
        GAME_OVER = True
        clear_movement_inputs()


def check_mission_success():
    global MISSION_SUCCESS
    if GAME_OVER or MISSION_SUCCESS or MISSION_FAILED:
        return
    if TREASURE_TAKEN and (thief_z <= EXIT_Z_THRESHOLD):
        MISSION_SUCCESS = True
        clear_movement_inputs()


def check_mission_failed():
    global MISSION_FAILED
    if GAME_OVER or MISSION_SUCCESS or MISSION_FAILED:
        return
    if (thief_z <= EXIT_Z_THRESHOLD) and (not TREASURE_TAKEN) and EVER_DETECTED:
        MISSION_FAILED = True
        clear_movement_inputs()


thief_radius = 0.8
ALERTED = False
ALERT_SOURCE = ""
ALERT_PERSIST_TIME = 3.0
last_seen_time = -9999.0
guard_symbol_timer = 0.0
cctv_symbol_timer = 0.0
player_spotted_timer = 0.0
alert_symbol_timer = 0.0
ALERT_SYMBOL_DURATION = 1.5
GUARD_SYMBOL_DURATION = 2.0
CCTV_SYMBOL_DURATION = 2.0
SPOTTED_SYMBOL_DURATION = 1.5
GUARD_STATE_PATROL = 0
GUARD_STATE_CHASE = 1
GUARD_STATE_INVESTIGATE = 2
INVESTIGATE_REACH_DIST = 1.2
cctv_last_detect_x = 0.0
cctv_last_detect_z = 0.0
cctv_has_target = False
high_alert_timer = 0.0
HIGH_ALERT_DURATION = 6.0
guard_x = 0.0
guard_z = 0.0
guard_dir_angle = 180.0
GUARD_STATE_PATROL = 0
GUARD_STATE_CHASE = 1
guard_state = GUARD_STATE_PATROL
guard_patrol_points = [
    (-6.0, -8.0),
    (6.0, -8.0),
    (6.0, 8.0),
    (-6.0, 8.0),
]
30
guard_patrol_i = 0
GUARD_PATROL_SPEED = 1.0
GUARD_CHASE_SPEED = 3.0
GUARD_INVESTIGATE_SPEED = 2.0
GUARD_VIEW_DIST = 8.0
GUARD_VIEW_FOV = 45.0
GUARD_PATROL_TURN_SPEED = 180.0
GUARD_INVEST_TURN_SPEED = 240.0
guard_walk_phase = 0.0
GUARD_STEP_FREQ = 6.0
GUARD_LEG_SWING = 28.0
GUARD_ARM_SWING = 18.0
CCTV_DIST = 10.0
CCTV_FOV = 35.0
CCTV_POWER_ON = True
POWER_BUTTON_RADIUS = 2.2
POWER_BUTTON_X = 0.0
POWER_BUTTON_Z = 0.0
is_hidden = False
hidden_spot_index = -1
HIDE_ENTER_RADIUS = 2.2
HIDE_EXIT_PUSH = 2.5
hide_spots = []
WALK_STEP = 0.7
RUN_MULT = 1.8
Camera_angle = math.pi
Camera_radius = 50.0
Camera_height = 25.0
Rotate_speed = 0.08
Height_speed = 0.6
Min_camera_height = 6.0
Max_camera_height = 60.0
TP_DISTANCE = 12.0
TP_HEIGHT = 6.5
TP_SIDE = 0.0
TP_LOOK_Y = 4.0
CAM_SMOOTH = 0.18
cam_follow_x = 0.0
cam_follow_y = TP_HEIGHT
cam_follow_z = 0.0
CCTV_Scan_Angle = 0.0
key_angle = 0.0
Tree_spacing = 2
Tree_positions = []
Door_width = 6.0
Door_height = 6.0
SOFA_SCALE_FACTOR = 0.04
BED_SCALE_FACTOR_SCENE = 0.04
ALMIRAH_SCALE_FACTOR_SCENE = 0.021
character_angle = 0.0
angle = 0.0
character_angle = 0.0
box_rot = 0.0
ROTATE_BOX = True
SKIN = (0.95, 0.80, 0.70)
BLACK = (0.0, 0.0, 0.0)
WHITE = (1.0, 1.0, 1.0)
GUARD_BROWN = (0.45, 0.30, 0.15)
STICK_COLOR = (0.30, 0.15, 0.05)


def _quadric():
    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)
    return q


def draw_sphere(r, slices=20, stacks=20):
    q = _quadric()
    gluSphere(q, r, slices, stacks)


def draw_cylinder(r1, r2, h, slices=20, stacks=1):
    q = _quadric()
    gluCylinder(q, r1, r2, h, slices, stacks)


def draw_disk(inner_r, outer_r, slices=30, loops=2):
    q = _quadric()
    gluDisk(q, inner_r, outer_r, slices, loops)


def draw_cuboid_char(w, h, d):
    glPushMatrix()
    glScalef(w, h, d)
    glutSolidCube(1)
    glPopMatrix()


def draw_robber_cap():
    glColor3fv(BLACK)
    glPushMatrix()
    glTranslatef(0.0, 1.07, 0.0)
    glScalef(1.0, 0.85, 1.0)
    draw_sphere(0.15, 24, 24)
    glPopMatrix()


def draw_thief(anim_time, _):
    glPushMatrix()
    LEG_SWING = 25.0
    ARM_SWING = 20.0
    leg_angle = math.sin(anim_time) * LEG_SWING
    arm_angle = math.sin(anim_time) * ARM_SWING
    global_scale = 3.5
    glScalef(global_scale, global_scale, global_scale)
    glColor3fv(BLACK)
    glPushMatrix()
    glTranslatef(-0.15, 0.5, 0.0)
    glRotatef(leg_angle, 1, 0, 0)
    glTranslatef(0.0, -0.25, 0.0)
    draw_cuboid_char(0.12, 0.5, 0.12)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.15, 0.5, 0.0)
    glRotatef(-leg_angle, 1, 0, 0)
    glTranslatef(0.0, -0.25, 0.0)
    draw_cuboid_char(0.12, 0.5, 0.12)
    glPopMatrix()
    stripe_h = 0.04
    for i in range(10):
        glColor3fv(BLACK if i % 2 == 0 else WHITE)
        glPushMatrix()
        glTranslatef(0.0, 0.5 + i * stripe_h, 0.0)
        draw_cuboid_char(0.40, stripe_h, 0.25)
        glPopMatrix()
    glColor3fv(SKIN)
    glPushMatrix()
    glTranslatef(-0.25, 0.8, 0.0)
    glRotatef(-arm_angle, 1, 0, 0)
    glTranslatef(0.0, -0.2, 0.0)
    draw_cuboid_char(0.10, 0.40, 0.10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.25, 0.8, 0.0)
    glRotatef(arm_angle, 1, 0, 0)
    glTranslatef(0.0, -0.2, 0.0)
    draw_cuboid_char(0.10, 0.40, 0.10)
    glPopMatrix()
    glColor3fv(SKIN)
    glPushMatrix()
    glTranslatef(0.0, 0.95, 0.0)
    draw_cuboid_char(0.10, 0.10, 0.10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.0, 1.05, 0.0)
    draw_sphere(0.13, 20, 20)
    glPopMatrix()
    draw_robber_cap()
    glPopMatrix()


def draw_guard_hat():
    glColor3fv(GUARD_BROWN)
    glPushMatrix()
    glTranslatef(0.0, 1.23, 0.0)
    glRotatef(-90, 1, 0, 0)
    draw_disk(0.07, 0.20, 28, 2)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.0, 1.23, 0.0)
    glRotatef(-90, 1, 0, 0)
    draw_cylinder(0.12, 0.12, 0.12, 28, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.0, 1.35, 0.0)
    glRotatef(-90, 1, 0, 0)
    draw_disk(0.0, 0.12, 28, 2)
    glPopMatrix()


def draw_guard(leg_angle, arm_angle):
    glPushMatrix()
    global_scale = 3.55
    glScalef(global_scale, global_scale, global_scale)
    glColor3fv(BLACK)
    glPushMatrix()
    glTranslatef(-0.15, 0.5, 0.0)
    glRotatef(leg_angle, 1, 0, 0)
    glTranslatef(0.0, -0.25, 0.0)
    draw_cuboid_char(0.12, 0.5, 0.12)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.15, 0.5, 0.0)
    glRotatef(-leg_angle, 1, 0, 0)
    glTranslatef(0.0, -0.25, 0.0)
    draw_cuboid_char(0.12, 0.5, 0.12)
    glPopMatrix()
    glColor3fv(GUARD_BROWN)
    glPushMatrix()
    glTranslatef(0.0, 0.6, 0.0)  # Pant
    draw_cuboid_char(0.35, 0.20, 0.22)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.0, 0.85, 0.0)  # Shirt
    draw_cuboid_char(0.40, 0.30, 0.25)
    glPopMatrix()
    glColor3fv(SKIN)
    glPushMatrix()
    glTranslatef(-0.25, 0.8, 0.0)
    glRotatef(-arm_angle * 0.6, 1, 0, 0)
    glTranslatef(0.0, -0.2, 0.0)
    draw_cuboid_char(0.10, 0.40, 0.10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.25, 0.83, 0.02)
    glRotatef(-55, 1, 0, 0)
    glRotatef(18, 0, 0, 1)
    glTranslatef(0.0, -0.2, 0.0)
    draw_cuboid_char(0.10, 0.40, 0.10)
    glColor3fv(STICK_COLOR)
    glPushMatrix()
    glTranslatef(0.03, -0.28, 0.02)
    glRotatef(90, 1, 0, 0)
    glRotatef(-6, 0, 0, 1)
    draw_cylinder(0.025, 0.025, 0.75, 14, 1)
    glPopMatrix()
    glPopMatrix()
    glColor3fv(SKIN)
    glPushMatrix()
    glTranslatef(0.0, 0.95, 0.0)
    draw_cuboid_char(0.10, 0.10, 0.10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.0, 1.15, 0.0)
    draw_sphere(0.13, 20, 20)
    glPopMatrix()
    draw_guard_hat()
    glPopMatrix()


def DrawKey(r, g, b):
    quad = gluNewQuadric()
    glPushMatrix()
    s = 0.04
    glScalef(s, s, s)
    glRotatef(90, 0, 1, 0)
    glColor3f(r, g, b)
    glPushMatrix()
    glutSolidTorus(2, 12, 20, 30)
    glPopMatrix()
    glColor3f(0.8, 0.8, 0.8)
    glPushMatrix()
    glTranslatef(18, 0, 0)
    glRotatef(90, 0, 1, 0)
    gluCylinder(quad, 3, 3, 40, 20, 20)
    glPopMatrix()
    teeth_positions = [20, 27, 34]
    for t in teeth_positions:
        glPushMatrix()
        glTranslatef(18 + t, -10, -2)
        glScalef(4, 16, 4)
        glutSolidCube(1)
        glPopMatrix()
    glPopMatrix()


def DrawRoundTable():
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 0.5, 0.5, 2.2, 20, 5)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0.2, 0)
    glRotatef(-90, 1, 0, 0)
    gluDisk(gluNewQuadric(), 0, 1.5, 20, 5)
    glPopMatrix()
    glColor3f(0.5, 0.25, 0.15)
    glPushMatrix()
    glTranslatef(0, 2.2, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 2.5, 2.5, 0.2, 30, 5)
    glTranslatef(0, 0, 0.2)
    gluDisk(gluNewQuadric(), 0, 2.5, 30, 5)
    glPopMatrix()


def DrawBox(width, height, depth):
    w = width / 2
    d = depth / 2
    glBegin(GL_QUADS)
    glVertex3f(-w, 0, d);
    glVertex3f(w, 0, d);
    glVertex3f(w, height, d);
    glVertex3f(-w, height, d)
    glVertex3f(-w, 0, -d);
    glVertex3f(-w, height, -d);
    glVertex3f(w, height, -d);
    glVertex3f(w, 0, -d)
    glVertex3f(-w, 0, -d);
    glVertex3f(-w, 0, d);
    glVertex3f(-w, height, d);
    glVertex3f(-w, height, -d)
    glVertex3f(w, 0, -d);
    glVertex3f(w, height, -d);
    glVertex3f(w, height, d);
    glVertex3f(w, 0, d)
    glVertex3f(-w, height, d);
    glVertex3f(w, height, d);
    glVertex3f(w, height, -d);
    glVertex3f(-w, height, -d)
    glVertex3f(-w, 0, d);
    glVertex3f(-w, 0, -d);
    glVertex3f(w, 0, -d);
    glVertex3f(w, 0, d)
    glEnd()


def DrawCylinder(radius, height):
    slices = 16
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        angle = 2 * math.pi * i / slices
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        glVertex3f(x, height, z)
        glVertex3f(x, 0, z)
    glEnd()


def DrawPyramid(base_size, height):
    b = base_size / 2
    glBegin(GL_TRIANGLES)
    glVertex3f(0, height, 0);
    glVertex3f(-b, 0, b);
    glVertex3f(b, 0, b)
    glVertex3f(0, height, 0);
    glVertex3f(b, 0, b);
    glVertex3f(b, 0, -b)
    glVertex3f(0, height, 0);
    glVertex3f(b, 0, -b);
    glVertex3f(-b, 0, -b)
    glVertex3f(0, height, 0);
    glVertex3f(-b, 0, -b);
    glVertex3f(-b, 0, b)
    glEnd()


BED_LENGTH = 210
BED_WIDTH = 320
BED_HEIGHT = 40


def DrawBedBlock(x, y, z, sx, sy, sz, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glColor3f(*color)
    glutSolidCube(1)
    glPopMatrix()


def DrawBed():
    thickness = 10
    DrawBedBlock(0, 0, BED_HEIGHT / 2,
                 BED_LENGTH, BED_WIDTH, BED_HEIGHT,
                 (0.45, 0.25, 0.15))
    DrawBedBlock(0, 0, BED_HEIGHT + thickness / 2,
                 BED_LENGTH * 0.95, BED_WIDTH * 0.95, thickness,
                 (0.1, 0.6, 0.9))
    pillow_z = BED_HEIGHT + thickness + 6
    DrawBedBlock(-BED_LENGTH * 0.22, BED_WIDTH * 0.35, pillow_z,
                 BED_LENGTH * 0.25, BED_WIDTH * 0.15, 12, (1, 1, 1))
    DrawBedBlock(BED_LENGTH * 0.22, BED_WIDTH * 0.35, pillow_z,
                 BED_LENGTH * 0.25, BED_WIDTH * 0.15, 12, (1, 1, 1))
    DrawBedBlock(0, BED_WIDTH / 2 + 8, BED_HEIGHT + 30,
                 BED_LENGTH * 0.95, 16, 60, (0.35, 0.18, 0.1))
    leg_h = 30
    leg_w = 16
    for x in (-BED_LENGTH / 2 + leg_w, BED_LENGTH / 2 - leg_w):
        for y in (-BED_WIDTH / 2 + leg_w, BED_WIDTH / 2 - leg_w):
            DrawBedBlock(x, y, leg_h / 2, leg_w, leg_w, leg_h, (0.1, 0.1, 0.1))


def draw_almirah():
    width = 250
    depth = 100
    height = 160
    glPushMatrix()
    glColor3f(0.35, 0.18, 0.08)
    glTranslatef(0, 0, height / 2)
    glScalef(width, depth, height)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.5, 0.25, 0.1)
    glTranslatef(-width / 4, depth / 2 + 1, height / 2)
    glScalef(width / 2 - 2, 2, height - 10)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.5, 0.25, 0.1)
    glTranslatef(width / 4, depth / 2 + 1, height / 2)
    glScalef(width / 2 - 2, 2, height - 10)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.9, 0.8, 0.3)
    glPushMatrix()
    glTranslatef(-10, depth / 2 + 4, height / 2)
    glutSolidSphere(4, 20, 20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(10, depth / 2 + 4, height / 2)
    glutSolidSphere(4, 20, 20)
    glPopMatrix()


def cylinder_glut(x, y, z, r, h, color):
    glPushMatrix();
    glTranslatef(x, y, z);
    glColor3f(*color);
    gluCylinder(gluNewQuadric(), r, r, h, 20, 5);
    glPopMatrix()


def DrawSofaObject(seats):
    seat_width = 80
    total_width = seats * seat_width
    glPushMatrix();
    glColor3f(0.4, 0.2, 0.1);
    glTranslatef(0, 0, 20);
    glScalef(total_width, 60, 20);
    glutSolidCube(1);
    glPopMatrix()
    for i in range(seats):
        x = -total_width / 2 + seat_width / 2 + i * seat_width
        glPushMatrix();
        glColor3f(0.1, 0.1, 0.1);
        glTranslatef(x, 0, 35);
        glScalef(seat_width - 5, 55, 15);
        glutSolidCube(1);
        glPopMatrix()
    glPushMatrix();
    glColor3f(0.5, 0.25, 0.15);
    glTranslatef(0, -25, 65);
    glScalef(total_width, 15, 60);
    glutSolidCube(1);
    glPopMatrix()
    glColor3f(0.45, 0.22, 0.12)
    glPushMatrix();
    glTranslatef(-total_width / 2 - 10, 0, 50);
    glScalef(20, 60, 50);
    glutSolidCube(1);
    glPopMatrix()
    glPushMatrix();
    glTranslatef(total_width / 2 + 10, 0, 50);
    glScalef(20, 60, 50);
    glutSolidCube(1);
    glPopMatrix()
    for lx in (-total_width / 2 + 15, total_width / 2 - 15):
        for ly in (-20, 20): cylinder_glut(lx, ly, 0, 5, 20, (0.1, 0.1, 0.1))


def DrawTable():
    glPushMatrix();
    glColor3f(0.8, 0.8, 0.8);
    glTranslatef(0, 2.0, 0);
    DrawBox(6.0, 0.2, 4.0);
    glPopMatrix()
    glColor3f(0.3, 0.15, 0.05)
    for x in [-2.5, 2.5]:
        for z in [-1.5, 1.5]: glPushMatrix(); glTranslatef(x, 0, z); DrawBox(0.3, 2.0, 0.3); glPopMatrix()


def DrawTreasureChest():
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    DrawBox(3.0, 1.5, 1.8)
    glPopMatrix()
    glColor3f(0.45, 0.25, 0.12)
    glPushMatrix()
    glTranslatef(0, 1.5, 0)
    DrawBox(3.0, 0.9, 1.8)
    glPopMatrix()
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(-0.9, 0.0, 0.01)
    glTranslatef(0, 0, 0.9)
    DrawBox(0.22, 2.1, 0.05)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.9, 0.0, 0.01)
    glTranslatef(0, 0, 0.9)
    DrawBox(0.22, 2.1, 0.05)
    glPopMatrix()
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(0, 1.2, 0.93)
    DrawBox(0.45, 0.6, 0.08)
    glPopMatrix()
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(0, 1.35, 0.98)
    DrawBox(0.12, 0.22, 0.02)
    glPopMatrix()


def FloorCreation():
    for r in range(-Grid_rows // 2, Grid_rows // 2):
        for c in range(-Grid_cols // 2, Grid_cols // 2):
            x1 = c * Floortile_size
            x2 = (c + 1) * Floortile_size
            z1 = r * Floortile_size
            z2 = (r + 1) * Floortile_size
            if (r + c) % 2 == 0:
                glColor3f(0.0, 0.0, 0.0)
            else:
                glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_QUADS)
            glVertex3f(x1, -1.45, z1);
            glVertex3f(x2, -1.45, z1);
            glVertex3f(x2, -1.45, z2);
            glVertex3f(x1, -1.45, z2)
            glEnd()


def CarpetBlock(x, y, z, sx, sy, sz, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glColor3f(*color)
    glutSolidCube(1)
    glPopMatrix()


def CarpetThread(x, y, z, sx, sy, sz, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glColor3f(*color)
    glutSolidCube(1)
    glPopMatrix()


def DrawHidingBox():
    glPushMatrix()
    s = 0.05
    glScalef(s, s, s)
    glRotatef(-90, 1, 0, 0)
    glTranslatef(0, 0, 0)
    glPushMatrix()
    glColor3f(0.5, 0.35, 0.25)
    glTranslatef(0, 0, 20)
    glScalef(80, 60, 40)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0, 0, 0)
    glTranslatef(0, 0, 20)
    glScalef(70, 50, 30)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.6, 0.4, 0.3)
    glTranslatef(0, -30, 50)
    glRotatef(-60, 1, 0, 0)
    glScalef(80, 60, 5)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(1, 0, 0)
    glRasterPos3f(-18, 10, 50)
    for ch in "HIDE":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glPopMatrix()


def DrawBigRoundTable():
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 0.6, 0.6, 2.2, 20, 5)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0.1, 0)
    glRotatef(-90, 1, 0, 0)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)  # Center
    for i in range(0, 361, 10):
        theta = math.radians(i)
        glVertex3f(2.2 * math.cos(theta), 2.2 * math.sin(theta), 0)
    glEnd()
    glPopMatrix()
    glColor3f(0.5, 0.25, 0.15)
    glPushMatrix()
    glTranslatef(0, 2.2, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4.5, 4.5, 0.3, 30, 5)
    glTranslatef(0, 0, 0.3)
    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(0, 0, 1)
    glVertex3f(0, 0, 0)  # Center
    for i in range(0, 361, 10):
        theta = math.radians(i)
        glVertex3f(4.5 * math.cos(theta), 4.5 * math.sin(theta), 0)
    glEnd()
    glPopMatrix()


def DrawCarpetScene():
    CARPET_LENGTH = 320
    CARPET_WIDTH = 200
    thickness = 4
    border = 14
    glPushMatrix()
    CarpetBlock(0, 0, thickness / 2,
                CARPET_LENGTH, CARPET_WIDTH, thickness,
                (0.55, 0.08, 0.12))  # Dark Red Base
    CarpetBlock(0, CARPET_WIDTH / 2 - border / 2, thickness + 0.1,
                CARPET_LENGTH, border, 1, (0.9, 0.75, 0.2))
    CarpetBlock(0, -CARPET_WIDTH / 2 + border / 2, thickness + 0.1,
                CARPET_LENGTH, border, 1, (0.9, 0.75, 0.2))
    CarpetBlock(CARPET_LENGTH / 2 - border / 2, 0, thickness + 0.1,
                border, CARPET_WIDTH, 1, (0.9, 0.75, 0.2))
    CarpetBlock(-CARPET_LENGTH / 2 + border / 2, 0, thickness + 0.1,
                border, CARPET_WIDTH, 1, (0.9, 0.75, 0.2))
    CarpetBlock(0, 0, thickness + 0.2,
                CARPET_LENGTH * 0.85, CARPET_WIDTH * 0.75, 1,
                (0.2, 0.2, 0.6))
    glPushMatrix()
    glTranslatef(0, 0, thickness + 0.3)
    glRotatef(45, 0, 0, 1)
    glScalef(CARPET_LENGTH * 0.25, CARPET_LENGTH * 0.25, 1)
    glColor3f(0.95, 0.95, 0.95)
    glutSolidCube(1)
    glPopMatrix()
    for i in range(-3, 4):
        CarpetBlock(i * (CARPET_LENGTH * 0.1), 0, thickness + 0.35,
                    8, CARPET_WIDTH * 0.55, 1,
                    (0.8, 0.8, 0.1))
    colors = [
        (1, 0, 0), (0, 1, 0), (0, 0, 1),
        (1, 1, 0), (1, 0, 1), (0, 1, 1)
    ]
    step = 10
    t_len = 14
    for i, x in enumerate(range(-CARPET_LENGTH // 2, CARPET_LENGTH // 2, step)):
        c = colors[i % len(colors)]
        CarpetThread(x, CARPET_WIDTH / 2 + 6, 2, t_len, 2, 2, c)
        CarpetThread(x, -CARPET_WIDTH / 2 - 6, 2, t_len, 2, 2, c)
    for i, y in enumerate(range(-CARPET_WIDTH // 2, CARPET_WIDTH // 2, step)):
        c = colors[i % len(colors)]
        CarpetThread(-CARPET_LENGTH / 2 - 6, y, 2, t_len, 2, 2, c)
        CarpetThread(CARPET_LENGTH / 2 + 6, y, 2, t_len, 2, 2, c)
    glPopMatrix()


def OuterBoundaryWalls():
    wall_height = 5.5
    wall_thickness = 1.0
    floor_level = -1.45
    glColor3f(0.5, 0.27, 0.07)
    glColor3f(0.5, 0.1, 0.1)
    glPushMatrix();
    glTranslatef(0, floor_level, Floor_length + wall_thickness / 2);
    DrawBox(Floor_width * 2, wall_height, wall_thickness);
    glPopMatrix()
    glPushMatrix();
    glTranslatef(-Floor_width - wall_thickness / 2, floor_level, 0);
    DrawBox(wall_thickness, wall_height, Floor_length * 2);
    glPopMatrix()
    glPushMatrix();
    glTranslatef(Floor_width + wall_thickness / 2, floor_level, 0);
    DrawBox(wall_thickness, wall_height, Floor_length * 2);
    glPopMatrix()
    w_seg = (Floor_width * 2 - Door_width) / 2
    glPushMatrix();
    glTranslatef(-Floor_width + w_seg / 2, floor_level, -Floor_length - wall_thickness / 2);
    DrawBox(w_seg, wall_height, wall_thickness);
    glPopMatrix()
    glPushMatrix();
    glTranslatef(Floor_width - w_seg / 2, floor_level, -Floor_length - wall_thickness / 2);
    DrawBox(w_seg, wall_height, wall_thickness);
    glPopMatrix()
    door_z_center = -Floor_length - wall_thickness / 2
    door_x_center = 0.0
    door_y_center = floor_level
    glPushMatrix()
    glTranslatef(door_x_center, door_y_center, door_z_center)
    if Door_open:
        glTranslatef(-Door_width / 2, 0, 0)
        glRotatef(90, 0, 1, 0)
        glTranslatef(Door_width / 2, 0, 0)
    glColor3f(1.0, 0.0, 0.0)
    DrawBox(Door_width, Door_height, wall_thickness)
    glPopMatrix()
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix();
    glTranslatef(Door_width / 4, floor_level + Door_height / 2, door_z_center - wall_thickness / 2 - 0.15);
    glutSolidSphere(0.2, 10, 10);
    glPopMatrix()
    glPushMatrix();
    glTranslatef(Door_width / 4, floor_level + Door_height / 2, door_z_center + wall_thickness / 2 + 0.15);
    glutSolidSphere(0.2, 10, 10);
    glPopMatrix()
    if wall_height > Door_height:
        glColor3f(0.5, 0.27, 0.07)
        glPushMatrix();
        glTranslatef(0, (floor_level + Door_height) - 0.05, door_z_center);
        DrawBox(Door_width, (wall_height - Door_height) + 0.05, wall_thickness);
        glPopMatrix()


def InnerBoundaryWalls():
    global TREASURE_TAKEN
    wall_height = 4.0
    wall_thickness = 1.0
    floor_level = -1.45
    part_width = (2 * Floor_width) / 3
    x1 = -Floor_width + part_width
    x2 = -Floor_width + 2 * part_width
    glColor3f(0.5, 0.27, 0.07)
    glPushMatrix();
    glTranslatef(x1, floor_level, 0);
    DrawBox(wall_thickness, wall_height, Floor_length * 2);
    glPopMatrix()
    glPushMatrix();
    glTranslatef(x2, floor_level, 0);
    DrawBox(wall_thickness, wall_height, Floor_length * 2);
    glPopMatrix()
    glPushMatrix();
    glTranslatef((-Floor_width + x1) / 2, floor_level, 0);
    DrawBox(part_width, wall_height, wall_thickness);
    glPopMatrix()
    glPushMatrix();
    glTranslatef((x2 + Floor_width) / 2, floor_level, 0);
    DrawBox(part_width, wall_height, wall_thickness);
    glPopMatrix()
    door_w, door_h, door_t = 4.0, 4.1, 1.2
    z_back, z_front = Floor_length / 2, -Floor_length / 2

    def DrawDoor(tx, ty, tz, r, g, b, angle_deg):
        glPushMatrix()
        glTranslatef(tx, ty, tz)
        glTranslatef(0, 0, -door_w / 2.0)
        glRotatef(angle_deg, 0, 1, 0)
        glTranslatef(0, 0, door_w / 2.0)
        glColor3f(r, g, b)
        DrawBox(door_t, door_h, door_w)
        glPopMatrix()
        glColor3f(0.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(tx + door_t / 2 + 0.15, ty + door_h / 2, tz + door_w / 4)
        glutSolidSphere(0.2, 10, 10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(tx - door_t / 2 - 0.15, ty + door_h / 2, tz + door_w / 4)
        glutSolidSphere(0.2, 10, 10)
        glPopMatrix()

    if has_blue_key == True:
        DrawDoor(x1, floor_level, z_back, 0, 0, 1, Door_blue_angle)  # Blue Room
    if has_green_key == True:
        DrawDoor(x1, floor_level, z_front, 0, 0.8, 0, Door_green_angle)  # Green Room Door
    if has_cyan_key == True:
        DrawDoor(x2, floor_level, z_back, 0, 1, 1, Door_cyan_angle)  # Cyan Room Door
    if has_purple_key == True:
        DrawDoor(x2, floor_level, z_front, 0.6, 0, 0.8, Door_purple_angle)
    mid_room_center_x = (x1 + x2) / 2
    mid_room_center_z = 0
    glPushMatrix()
    glTranslatef(mid_room_center_x, floor_level, mid_room_center_z)
    glRotatef(0, 0, 0, 1)
    glRotatef(-90, 1, 0, 0)
    glScalef(0.06, 0.06, 0.06)
    DrawCarpetScene()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(mid_room_center_x, floor_level, mid_room_center_z)
    DrawBigRoundTable()
    glPopMatrix()

    # key
    purple_key_x = 3
    purple_key_z = Floor_length - 3.0
    glPushMatrix()
    glTranslatef(purple_key_x, floor_level, purple_key_z)
    DrawRoundTable()
    glTranslatef(0, 3.0, 0)
    glRotatef(key_angle, 0, 1, 0)
    if purple_key_active:
        DrawKey(0.6, 0, 0.8)
    glPopMatrix()
    bed_room_x = x1 - 4.0
    bed_room_z = Floor_length - 4.0
    glPushMatrix()
    glTranslatef(bed_room_x, floor_level, bed_room_z)
    DrawRoundTable()
    glTranslatef(0, 3.0, 0)
    glRotatef(key_angle, 0, 1, 0)
    if cyan_key_active:
        DrawKey(0, 1, 1)
    glPopMatrix()
    blue_key_x = Floor_width - 5.0
    blue_key_z = -Floor_length + 5.0
    glPushMatrix()
    glTranslatef(blue_key_x, floor_level, blue_key_z)
    DrawRoundTable()
    glTranslatef(0, 3.0, 0)
    glRotatef(key_angle, 0, 1, 0)
    if has_blue_key == False:
        DrawKey(0, 0, 1)
    glPopMatrix()
    green_key_x = x2 + 5.0
    green_key_z = Floor_length - 4.0
    glPushMatrix()
    glTranslatef(green_key_x, floor_level, green_key_z)
    DrawRoundTable()
    glTranslatef(0, 3.0, 0)
    glRotatef(key_angle, 0, 1, 0)
    if has_green_key == False:
        DrawKey(0, 0.8, 0)
    glPopMatrix()
    bath_d = 8.0
    bath_w = 12.0
    bath_wall_h = 4.0
    bath_wall_t = 0.5
    glColor3f(0.4, 0.4, 0.45)
    glPushMatrix()
    bath_floor_x = -Floor_width + (bath_w / 2)
    bath_floor_z = Floor_length - (bath_d / 2)
    glTranslatef(bath_floor_x, floor_level + 0.02, bath_floor_z)
    glScalef(bath_w, 0.05, bath_d)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.95, 0.95, 0.95)
    glPushMatrix()
    glTranslatef(-Floor_width + bath_w, floor_level, Floor_length - (bath_d / 2))
    DrawBox(bath_wall_t, bath_wall_h, bath_d)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-Floor_width + 2.0, floor_level, Floor_length - bath_d)
    DrawBox(4.0, bath_wall_h, bath_wall_t)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-Floor_width + bath_w - 2.0, floor_level, Floor_length - bath_d)
    DrawBox(4.0, bath_wall_h, bath_wall_t)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-Floor_width + 6.0, floor_level, Floor_length - bath_d)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.9, 0.9, 0.95)
    DrawBox(bath_wall_t * 2, 3.2, 4.0)
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0.6, 1.6, 1.2)
    glutSolidSphere(0.15, 10, 10)
    glPopMatrix()
    glColor3f(0.75, 0.75, 0.8)
    glPushMatrix()
    glTranslatef(0.55, 1.35, 1.2)
    glScalef(0.05, 0.25, 0.15)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(0.58, 1.35, 1.2)
    glScalef(0.02, 0.08, 0.02)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(-0.6, 1.6, 1.2)
    glutSolidSphere(0.15, 10, 10)
    glPopMatrix()
    glColor3f(0.75, 0.75, 0.8)
    glPushMatrix()
    glTranslatef(-0.55, 1.35, 1.2)
    glScalef(0.05, 0.25, 0.15)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(-0.58, 1.35, 1.2)
    glScalef(0.02, 0.08, 0.02)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()
    glPushMatrix()
    tub_x = -Floor_width + 4.0
    tub_z = Floor_length - (bath_d / 2)
    glTranslatef(tub_x, floor_level + 1.0, tub_z)
    glScalef(2.2, 2.2, 2.2)
    DrawBathtub()
    glPopMatrix()
    glPushMatrix()
    com_x = -Floor_width + bath_w - 2.5
    com_z = Floor_length - (bath_d / 2)
    glTranslatef(com_x, floor_level, com_z)
    glRotatef(-90, 0, 1, 0)
    glScalef(1.5, 1.5, 1.5)
    DrawCommode()
    glPopMatrix()
    glPushMatrix()
    tub_x = -Floor_width + 4.0
    tub_z = Floor_length - (bath_d / 2)
    glTranslatef(tub_x, floor_level + 1.0, tub_z)
    glScalef(2.2, 2.2, 2.2)
    DrawBathtub()
    glPopMatrix()
    glPushMatrix()
    com_x = -Floor_width + bath_w - 2.5
    com_z = Floor_length - (bath_d / 2)
    glTranslatef(com_x, floor_level, com_z)
    glRotatef(-90, 0, 1, 0)
    glScalef(1.5, 1.5, 1.5)
    DrawCommode()
    glPopMatrix()
    chest_x = -Floor_width + 5.0
    chest_z = -Floor_length + 1.0
    glPushMatrix()
    glTranslatef(chest_x, floor_level, chest_z)
    glRotatef(0, 0, 1, 0)
    if not TREASURE_TAKEN:
        DrawTreasureChest()
    glPopMatrix()
    cam_y, light_radius, back_wall_z = wall_height - 0.4, 8.0, Floor_length - (wall_thickness / 2) - 0.5
    cam_x = -Floor_width + 2.0
    cam_z = -Floor_length + 2.0
    desired_yaw = angle_to_target_deg(cam_x, cam_z, chest_x, chest_z)
    rot_angle = desired_yaw - 15.0
    DrawCCTV(cam_x, cam_y, cam_z, rot_angle,
             -Floor_width, x1, -Floor_length, Floor_length, light_radius)

    mid_min_x, mid_max_x = x1 + wall_thickness / 2, x2 - wall_thickness / 2
    DrawCCTV((mid_min_x + mid_max_x) / 2, cam_y, back_wall_z, 180 + CCTV_Scan_Angle, mid_min_x, mid_max_x,
             -Floor_length, Floor_length, light_radius)

    DrawCCTV(Floor_width - 7, cam_y, back_wall_z, 270, x2, Floor_width, -Floor_length, Floor_length, light_radius)
    group_center_x = (x2 + Floor_width) / 2
    group_center_z = -Floor_length + 15.0
    group_center_y = floor_level
    glPushMatrix();
    glTranslatef(group_center_x, group_center_y, group_center_z);
    DrawTable();
    glPopMatrix()
    glPushMatrix();
    glTranslatef(group_center_x, group_center_y, group_center_z - 5.0);
    glScalef(SOFA_SCALE_FACTOR, SOFA_SCALE_FACTOR, SOFA_SCALE_FACTOR);
    glRotatef(-90, 1, 0, 0);
    glRotatef(180, 0, 0, 1);
    DrawSofaObject(2);
    glPopMatrix()
    glPushMatrix();
    glTranslatef(group_center_x, group_center_y, group_center_z + 5.0);
    glScalef(SOFA_SCALE_FACTOR, SOFA_SCALE_FACTOR, SOFA_SCALE_FACTOR);
    glRotatef(-90, 1, 0, 0);
    DrawSofaObject(2);
    glPopMatrix()
    glPushMatrix();
    glTranslatef(group_center_x + 6.0, group_center_y, group_center_z);
    glScalef(SOFA_SCALE_FACTOR, SOFA_SCALE_FACTOR, SOFA_SCALE_FACTOR);
    glRotatef(-90, 1, 0, 0);
    glRotatef(90, 0, 0, 1);
    DrawSofaObject(1);
    glPopMatrix()
    glPushMatrix();
    glTranslatef(group_center_x - 6.0, group_center_y, group_center_z);
    glScalef(SOFA_SCALE_FACTOR, SOFA_SCALE_FACTOR, SOFA_SCALE_FACTOR);
    glRotatef(-90, 1, 0, 0);
    glRotatef(-90, 0, 0, 1);
    DrawSofaObject(1);
    glPopMatrix()
    almirah_depth_scaled = 40 * ALMIRAH_SCALE_FACTOR_SCENE
    almirah_x_pos = x1 - (almirah_depth_scaled / 2) - 0.2
    z_offset1 = 9
    z_offset2 = -9
    glPushMatrix()
    glTranslatef(almirah_x_pos, floor_level, (Floor_length * 0.5) - z_offset1)
    glRotatef(-90, 1, 0, 0)
    glRotatef(90, 0, 0, 1)
    glScalef(ALMIRAH_SCALE_FACTOR_SCENE, ALMIRAH_SCALE_FACTOR_SCENE, ALMIRAH_SCALE_FACTOR_SCENE)
    draw_almirah()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(almirah_x_pos, floor_level, (-Floor_length * 0.5) + z_offset2)
    glRotatef(-90, 1, 0, 0)
    glRotatef(90, 0, 0, 1)
    glScalef(ALMIRAH_SCALE_FACTOR_SCENE, ALMIRAH_SCALE_FACTOR_SCENE, ALMIRAH_SCALE_FACTOR_SCENE)
    draw_almirah()
    glPopMatrix()
    bed_half_length = (320 * BED_SCALE_FACTOR_SCENE) / 2
    bed_x_pos = -Floor_width + bed_half_length + 0.5
    glPushMatrix()
    glTranslatef(bed_x_pos, floor_level, (Floor_length * 0.5) - 4.0)
    glRotatef(-90, 1, 0, 0)
    glRotatef(90, 0, 0, 1)
    glScalef(BED_SCALE_FACTOR_SCENE, BED_SCALE_FACTOR_SCENE, BED_SCALE_FACTOR_SCENE)
    DrawBed()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(bed_x_pos, floor_level, -Floor_length * 0.5)
    glRotatef(-90, 1, 0, 0)
    glRotatef(90, 0, 0, 1)
    glScalef(BED_SCALE_FACTOR_SCENE, BED_SCALE_FACTOR_SCENE, BED_SCALE_FACTOR_SCENE)
    DrawBed()
    glPopMatrix()
    kitchen_center_x = (x2 + Floor_width) / 2
    kitchen_center_z = Floor_length * 0.5
    glPushMatrix()
    glTranslatef(kitchen_center_x, floor_level, kitchen_center_z)
    DrawDiningSet()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(Floor_width - 2.0, floor_level, 5.0)
    glRotatef(-90, 0, 1, 0)
    DrawFridge()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(Floor_width - 2.2, floor_level, 11.0)
    glRotatef(-90, 0, 1, 0)
    DrawGasStove()
    glPopMatrix()
    DrawPowerButton(floor_level)
    glPushMatrix()
    glTranslatef(-Floor_width + 15.0, floor_level, Floor_length - 2.0)
    glRotatef(-45, 0, 1, 0)
    DrawHidingBox()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(x2 - 22.0, floor_level, -Floor_length + 20.0)
    glRotatef(45, 0, 1, 0)
    DrawHidingBox()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(x2 + 8.0, floor_level, Floor_length - 22.0)
    glRotatef(-135, 0, 1, 0)
    DrawHidingBox()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(Floor_width - 20.0, floor_level, -Floor_length + 22.0)
    glRotatef(135, 0, 1, 0)
    DrawHidingBox()
    glPopMatrix()
    glPushMatrix()
    temp_thief_x = 0.0
    temp_thief_z = -Floor_length - 15.0
    glTranslatef(temp_thief_x, floor_level, temp_thief_z)
    glTranslatef(thief_x, floor_level, thief_z)
    glRotatef(180, 0, 1, 0)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(guard_x, floor_level, guard_z)
    guard_render_angle = (guard_dir_angle - 180.0) % 360.0
    glRotatef(guard_render_angle, 0, 1, 0)
    leg_anim = math.sin(guard_walk_phase) * GUARD_LEG_SWING
    arm_anim = math.sin(guard_walk_phase) * GUARD_ARM_SWING
    draw_guard(leg_anim, arm_anim)
    glPopMatrix()
    guard_facing = clamp_angle_deg(guard_dir_angle)
    eye_height = floor_level + 3.85
    eye_forward = 0.8
    rad = math.radians(guard_facing)
    fx = math.sin(rad)
    fz = math.cos(rad)
    eye_x = guard_x + fx * eye_forward
    eye_z = guard_z + fz * eye_forward
    eye_y = eye_height
    now_t = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    if ALERTED and ALERT_SOURCE == "GUARD":
        ray_color = (1.0, 0.0, 0.0)
    elif high_alert_timer > 0.0:
        # Flicker red/yellow
        ray_color = (1.0, 0.0, 0.0) if (int(now_t * 10) % 2 == 0) else (1.0, 1.0, 0.0)
    else:
        ray_color = (0.0, 1.0, 0.0)
    draw_detection_rays(
        eye_x, eye_y, eye_z,
        guard_facing,
        GUARD_VIEW_FOV,
        GUARD_VIEW_DIST,
        ray_color
    )
    if guard_symbol_timer > 0.0 and ALERT_SOURCE == "GUARD":
        draw_billboard_symbol(guard_x, floor_level + 4.6, guard_z, "!", (1.0, 0.0, 0.0), scale=0.016, line_w=4.5)


def DrawBathtub():
    glColor3f(0.6, 0.8, 1.0)
    glPushMatrix()
    glScalef(1.0, 0.8, 2.2)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.3, 0.6, 0.9)
    glPushMatrix()
    glTranslatef(0, 0.45, 0)
    glScalef(0.85, 0.05, 2.0)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(0, 0.6, 1.1)
    glutSolidCube(0.25)
    glPopMatrix()


def DrawCommode():
    glColor3f(1.0, 1.0, 1.0)
    glPushMatrix()
    glTranslatef(0, 1.0, -0.6)
    glScalef(1.2, 1.0, 0.5)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 0.2)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 0.35, 0.4, 0.8, 20, 5)
    glTranslatef(0, 0, 0.8)
    glColor3f(0.95, 0.95, 0.95)
    gluDisk(gluNewQuadric(), 0, 0.4, 20, 5)
    glPopMatrix()


# SUCCESSFUL
def DrawCCTV(x, y, z, rotate_y, rx_min, rx_max, rz_min, rz_max, rad):
    global ALERTED, ALERT_SOURCE
    global alert_symbol_timer, player_spotted_timer
    global cctv_last_detect_x, cctv_last_detect_z, cctv_has_target
    global CHEAT_MODE, CHEAT_INVISIBLE
    global camera_off_on
    if CHEAT_MODE and CHEAT_INVISIBLE:
        return
    if not CCTV_POWER_ON:
        return
    glPushMatrix();
    glTranslatef(x, y, z);
    glRotatef(rotate_y, 0, 1, 0)
    glColor3f(0.2, 0.2, 0.2);
    glPushMatrix();
    glTranslatef(0, 0, 0.3);
    DrawBox(0.4, 0.2, 0.6);
    glPopMatrix()
    glColor3f(0.0, 0.0, 0.0);
    glPushMatrix();
    glTranslatef(0, 0, 0.6);
    DrawBox(0.3, 0.3, 0.05);
    glPopMatrix()
    glPopMatrix()
    cctv_facing = clamp_angle_deg(rotate_y)

    detected = False

    if not is_hidden:
        detected = point_in_fov(x, z, cctv_facing, thief_x, thief_z, CCTV_DIST, CCTV_FOV)
        if detected and (not has_line_of_sight(x, z, thief_x, thief_z)):
            detected = False

    if detected:
        if not ALERTED:
            alert_symbol_timer = ALERT_SYMBOL_DURATION
            player_spotted_timer = SPOTTED_SYMBOL_DURATION
        cctv_last_detect_x = x
        cctv_last_detect_z = z
        cctv_has_target = True

        trigger_alert("CCTV")
        ray_color = (1.0, 0.0, 0.0)
    else:
        ray_color = (1.0, 1.0, 0.0)

    draw_detection_rays(x, y, z, cctv_facing, CCTV_FOV, CCTV_DIST, ray_color, ray_count=30)
    if cctv_symbol_timer > 0.0 and detected:
        draw_billboard_symbol(x, y + 1.6, z, "!", (1.0, 0.0, 0.0), scale=0.014, line_w=4.0)


def Nature():
    trunk_r, trunk_h = 0.35, 4.0
    for pos in Tree_positions:
        x, z = pos
        glPushMatrix();
        glTranslatef(x, -1.45, z);
        glColor3f(0.55, 0.27, 0.07);
        DrawCylinder(trunk_r, trunk_h);
        glTranslatef(0, trunk_h - 0.5, 0);
        glColor3f(0, 0.6, 0);
        DrawPyramid(3.0, 3.0);
        glPopMatrix()
    z_pos = -Floor_length - 20.0 + 0.5
    while z_pos <= -Floor_length:
        for x in [-Door_width / 2 - 1, Door_width / 2 + 1]:
            glPushMatrix();
            glTranslatef(x, -1.45, z_pos);
            glColor3f(0.55, 0.27, 0.07);
            DrawCylinder(trunk_r, trunk_h);
            glTranslatef(0, trunk_h - 0.5, 0);
            glColor3f(0, 0.6, 0);
            DrawPyramid(3.0, 3.0);
            glPopMatrix()
        z_pos += Tree_spacing


def DrawPathOutside():
    w = Door_width
    glColor3f(0.6, 0.4, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-w / 2, -1.44, -Floor_length - 20);
    glVertex3f(w / 2, -1.44, -Floor_length - 20);
    glVertex3f(w / 2, -1.44, -Floor_length);
    glVertex3f(-w / 2, -1.44, -Floor_length)
    glEnd()


def PlaceTrees():
    global Tree_positions
    offset = 1.5;
    x = -Floor_width - offset
    while x <= Floor_width + offset:
        if not (-Door_width / 2 <= x <= Door_width / 2): Tree_positions.append((x, -Floor_length - offset))
        Tree_positions.append((x, Floor_length + offset));
        x += Tree_spacing
    z = -Floor_length - offset + Tree_spacing
    while z < Floor_length + offset:
        Tree_positions.append((-Floor_width - offset, z));
        Tree_positions.append((Floor_width + offset, z));
        z += Tree_spacing


def DrawChair(scale):
    """Draws a simple chair"""
    glPushMatrix()
    glScalef(scale, scale, scale)
    leg_h, leg_w = 2.0, 0.25
    seat_size = 1.8
    seat_thick = 0.2
    back_h = 2.5
    glColor3f(0.2, 0.1, 0.05)
    offset = seat_size / 2 - 0.2
    for x in [-offset, offset]:
        for z in [-offset, offset]:
            glPushMatrix()
            glTranslatef(x, 0, z)
            DrawBox(leg_w, leg_h, leg_w)
            glPopMatrix()
    glColor3f(0.35, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(0, leg_h, 0)
    DrawBox(seat_size, seat_thick, seat_size)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-offset, leg_h + seat_thick, 0)
    DrawBox(0.2, back_h, seat_size)
    glPopMatrix()
    glPopMatrix()


def DrawDiningSet():
    table_w, table_h, table_d = 8.0, 3.2, 5.0
    glPushMatrix()
    # Table Legs
    glColor3f(0.25, 0.15, 0.1)
    leg_thick = 0.5
    offset_w = table_w / 2 - 0.5
    offset_d = table_d / 2 - 0.5
    for x in [-offset_w, offset_w]:
        for z in [-offset_d, offset_d]:
            glPushMatrix()
            glTranslatef(x, 0, z)
            DrawBox(leg_thick, table_h, leg_thick)
            glPopMatrix()
    glColor3f(0.4, 0.25, 0.15)
    glPushMatrix()
    glTranslatef(0, table_h, 0)
    DrawBox(table_w, 0.2, table_d)
    glPopMatrix()
    glPopMatrix()
    chair_scale = 1.0
    chair_z_offset = table_d / 2 + 0.8
    chair_x_offset = table_w / 2 + 0.8
    for x_pos in [-2.0, 2.0]:
        glPushMatrix()
        glTranslatef(x_pos, 0, chair_z_offset)
        glRotatef(90, 0, 1, 0)
        DrawChair(chair_scale)
        glPopMatrix()
    for x_pos in [-2.0, 2.0]:
        glPushMatrix()
        glTranslatef(x_pos, 0, -chair_z_offset)
        glRotatef(-90, 0, 1, 0)
        DrawChair(chair_scale)
        glPopMatrix()
    glPushMatrix()
    glTranslatef(-chair_x_offset, 0, 0)
    glRotatef(0, 0, 1, 0)
    DrawChair(chair_scale)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(chair_x_offset, 0, 0)
    glRotatef(180, 0, 1, 0)
    DrawChair(chair_scale)
    glPopMatrix()


def DrawFridge():
    w, h, d = 3.0, 6.5, 2.5
    glColor3f(0.9, 0.9, 0.95)
    glPushMatrix()
    glTranslatef(0, 0, 0)
    DrawBox(w, h, d)
    glPopMatrix()
    glColor3f(0.7, 0.7, 0.7)
    glPushMatrix()
    glTranslatef(0, h * 0.7, d / 2 + 0.01)
    DrawBox(w, 0.05, 0.02)
    glPopMatrix()
    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(-w / 3, h * 0.5, d / 2 + 0.1)
    DrawBox(0.2, 1.0, 0.1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-w / 3, h * 0.8, d / 2 + 0.1)
    DrawBox(0.2, 0.8, 0.1)
    glPopMatrix()


def DrawPowerButton(floor_level):
    body_w = 1.2
    body_h = 1.2
    body_t = 0.22
    glPushMatrix()
    glTranslatef(POWER_BUTTON_X, floor_level + 4.0, POWER_BUTTON_Z)
    glRotatef(-90, 0, 1, 0)
    glColor3f(0.15, 0.15, 0.15)
    glPushMatrix()
    DrawBox(body_t, body_h, body_w)
    glPopMatrix()
    if CCTV_POWER_ON:
        glColor3f(0.1, 0.9, 0.2)
    else:
        glColor3f(0.9, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(body_t / 2 + 0.06, 0.05, 0.0)
    glutSolidSphere(0.22, 16, 16)
    glPopMatrix()
    glPopMatrix()


def DrawGasStove():
    w, h, d = 3.5, 3.2, 2.5
    glColor3f(0.2, 0.2, 0.25)
    glPushMatrix()
    glTranslatef(0, 0, 0)
    DrawBox(w, h, d)
    glPopMatrix()
    glColor3f(0.7, 0.7, 0.7)
    glPushMatrix()
    glTranslatef(0, h, 0)
    DrawBox(w, 0.2, d)
    glPopMatrix()
    glColor3f(0.1, 0.1, 0.1)
    for x in [-0.8, 0.8]:
        glPushMatrix()
        glTranslatef(x, h + 0.15, 0)
        glRotatef(90, 1, 0, 0)
        glutSolidTorus(0.1, 0.4, 5, 10)
        glPopMatrix()


def Animate():
    global CCTV_Scan_Angle, key_angle
    global ALERTED, ALERT_SOURCE, last_seen_time
    global guard_symbol_timer, cctv_symbol_timer, player_spotted_timer
    global alert_symbol_timer, high_alert_timer
    global last_anim_time
    global thief_x, thief_z, thief_dir_angle, thief_leg_anim
    global GAME_OVER, MISSION_SUCCESS, MISSION_FAILED
    global TREASURE_TAKEN, EVER_DETECTED
    global run_down
    global has_blue_key, has_green_key, has_cyan_key, has_purple_key
    global CHEAT_MODE, CHEAT_ALL_KEYS

    if CHEAT_MODE and CHEAT_ALL_KEYS:
        has_blue_key = has_green_key = has_cyan_key = has_purple_key = True

    now = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    dt = now - last_anim_time
    if dt <= 0.0 or dt > 0.05:
        dt = 0.016
    last_anim_time = now
    guard_symbol_timer = max(0.0, guard_symbol_timer - dt)
    cctv_symbol_timer = max(0.0, cctv_symbol_timer - dt)
    player_spotted_timer = max(0.0, player_spotted_timer - dt)
    alert_symbol_timer = max(0.0, alert_symbol_timer - dt)
    high_alert_timer = max(0.0, high_alert_timer - dt)
    if is_hidden:
        thief_leg_anim = 0.0
        clear_movement_inputs()
    if GAME_OVER or MISSION_SUCCESS or MISSION_FAILED:
        clear_movement_inputs()
        glutPostRedisplay()
        return
    turn_speed = 140.0
    if key_down[b'a']:
        thief_dir_angle = (thief_dir_angle + turn_speed * dt) % 360.0
    if key_down[b'd']:
        thief_dir_angle = (thief_dir_angle - turn_speed * dt) % 360.0
    move_dir = 0.0
    if key_down[b'w']:
        move_dir += 1.0
    if key_down[b's']:
        move_dir -= 1.0
    if move_dir != 0.0:
        running = run_down
        move_speed = 12.5 * (RUN_MULT if running else 1.0)
        rad = math.radians(thief_dir_angle)
        fx = math.sin(rad)
        fz = math.cos(rad)
        nx = thief_x + fx * move_speed * dt * move_dir
        nz = thief_z + fz * move_speed * dt * move_dir
        if not check_collision(nx, nz):
            thief_x, thief_z = nx, nz
            thief_leg_anim += 10 if running else 6
            try_auto_hide()
    CCTV_Scan_Angle = 60.0 * math.sin(glutGet(GLUT_ELAPSED_TIME) / 2000.0)
    key_angle = (key_angle + 0.5) % 360
    try_auto_hide()
    guard_detection_update()
    guard_ai_update(dt)
    check_caught()
    if GAME_OVER:
        glutPostRedisplay()
        return
    check_mission_success()
    if MISSION_SUCCESS:
        glutPostRedisplay()
        return
    check_mission_failed()
    if MISSION_FAILED:
        glutPostRedisplay()
        return
    now = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    if ALERTED and (now - last_seen_time) > ALERT_PERSIST_TIME:
        if ALERT_SOURCE == "CCTV":
            high_alert_timer = HIGH_ALERT_DURATION
        ALERTED = False
        ALERT_SOURCE = ""
    glutPostRedisplay()


def draw_screen_text(x, y, text, color=(1.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_18):
    glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    w = glutGet(GLUT_WINDOW_WIDTH)
    h = glutGet(GLUT_WINDOW_HEIGHT)
    gluOrtho2D(0, w, 0, h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(*color)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopAttrib()


def Display_Scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if FIRST_PERSON:
        eye_x = thief_x
        eye_y = TP_HEIGHT
        eye_z = thief_z
        rad = math.radians(thief_dir_angle)
        look_x = eye_x + math.sin(rad)
        look_z = eye_z + math.cos(rad)
        gluLookAt(
            eye_x, eye_y, eye_z,
            look_x, eye_y, look_z,
            0, 1, 0
        )
    else:
        global cam_follow_x, cam_follow_y, cam_follow_z
        rad = math.radians(thief_dir_angle)
        forward_x = math.sin(rad)
        forward_z = math.cos(rad)
        right_x = math.sin(rad + math.pi / 2)
        right_z = math.cos(rad + math.pi / 2)
        desired_x = thief_x - forward_x * TP_DISTANCE + right_x * TP_SIDE
        desired_y = TP_HEIGHT
        desired_z = thief_z - forward_z * TP_DISTANCE + right_z * TP_SIDE
        cam_follow_x += (desired_x - cam_follow_x) * CAM_SMOOTH
        cam_follow_y += (desired_y - cam_follow_y) * CAM_SMOOTH
        cam_follow_z += (desired_z - cam_follow_z) * CAM_SMOOTH
        gluLookAt(
            cam_follow_x, cam_follow_y, cam_follow_z,
            thief_x, TP_LOOK_Y, thief_z,
            0, 1, 0
        )
    FloorCreation()
    OuterBoundaryWalls()
    InnerBoundaryWalls()
    DrawPathOutside()
    Nature()
    if not is_hidden:
        glPushMatrix()
        glTranslatef(thief_x, -1.45, thief_z)
        glRotatef((thief_dir_angle - 180.0) % 360.0, 0, 1, 0)
        draw_thief(thief_leg_anim, thief_leg_anim)
        glPopMatrix()
    if player_spotted_timer > 0.0:
        draw_billboard_symbol(thief_x, 4.2, thief_z, "?", (0.2, 0.4, 1.0), scale=0.015, line_w=4.0)
    w = glutGet(GLUT_WINDOW_WIDTH)
    h = glutGet(GLUT_WINDOW_HEIGHT)

    if GAME_OVER:
        draw_screen_text(w * 0.36, h * 0.55, "YOU ARE CAUGHT!", (1, 0, 0), GLUT_BITMAP_TIMES_ROMAN_24)
        draw_screen_text(w * 0.34, h * 0.48, "Press R to restart", (1, 1, 1))

    elif MISSION_SUCCESS:
        draw_screen_text(w * 0.30, h * 0.55, "MISSION SUCCESSFUL!", (0.2, 1, 0.2), GLUT_BITMAP_TIMES_ROMAN_24)
        draw_screen_text(w * 0.34, h * 0.48, "Press R to restart", (1, 1, 1))

    elif MISSION_FAILED:
        draw_screen_text(w * 0.33, h * 0.55, "MISSION SUCCESSFUL!", (1, 0.3, 0.3), GLUT_BITMAP_TIMES_ROMAN_24)
        draw_screen_text(w * 0.34, h * 0.48, "Press R to restart", (1, 1, 1))
    glutSwapBuffers()


def ArrowKeyControl(key, x, y):
    global thief_dir_angle, FIRST_PERSON
    global TP_HEIGHT, Min_camera_height, Max_camera_height
    global is_hidden
    if is_hidden:
        glutPostRedisplay()
        return
    look_speed = 4.0
    height_step = 0.8

    if FIRST_PERSON:
        if key == GLUT_KEY_LEFT:
            thief_dir_angle = (thief_dir_angle + look_speed) % 360.0
        elif key == GLUT_KEY_RIGHT:
            thief_dir_angle = (thief_dir_angle - look_speed) % 360.0
        elif key == GLUT_KEY_UP:
            TP_HEIGHT = min(Max_camera_height, TP_HEIGHT + height_step)
        elif key == GLUT_KEY_DOWN:
            TP_HEIGHT = max(Min_camera_height, TP_HEIGHT - height_step)
    else:
        if key == GLUT_KEY_UP:
            TP_HEIGHT = min(Max_camera_height, TP_HEIGHT + height_step)
        elif key == GLUT_KEY_DOWN:
            TP_HEIGHT = max(Min_camera_height, TP_HEIGHT - height_step)
    glutPostRedisplay()


sofa_rot = 0.0
almirah_rot = 0.0
table_set_rot = 0.0


def idle():
    global sofa_rot, almirah_rot, table_set_rot, box_rot
    global character_angle
    character_angle += 0.15
    if ROTATE_BOX:
        box_rot += 0.2
    global Door_angle
    target_angle = 90.0 if Door_open else 0.0
    global Door_blue_angle, Door_purple_angle, Door_cyan_angle, Door_green_angle
    target = 90.0
    Door_blue_angle = min(Door_blue_angle + DOOR_SPEED, target) if Door_blue_open else max(Door_blue_angle - DOOR_SPEED,
                                                                                           0.0)
    Door_purple_angle = min(Door_purple_angle + DOOR_SPEED, target) if Door_purple_open else max(
        Door_purple_angle - DOOR_SPEED, 0.0)
    Door_cyan_angle = min(Door_cyan_angle + DOOR_SPEED, target) if Door_cyan_open else max(Door_cyan_angle - DOOR_SPEED,
                                                                                           0.0)
    Door_green_angle = min(Door_green_angle + DOOR_SPEED, target) if Door_green_open else max(
        Door_green_angle - DOOR_SPEED, 0.0)
    if Door_angle < target_angle:
        Door_angle = min(Door_angle + DOOR_SPEED, target_angle)
    elif Door_angle > target_angle:
        Door_angle = max(Door_angle - DOOR_SPEED, target_angle)
    glutPostRedisplay()


def restart_game():
    global thief_x, thief_z, thief_dir_angle, thief_leg_anim
    global ALERTED, ALERT_SOURCE, last_seen_time
    global guard_symbol_timer, cctv_symbol_timer, player_spotted_timer
    global alert_symbol_timer, high_alert_timer
    global is_hidden, hidden_spot_index
    global GAME_OVER, MISSION_SUCCESS, MISSION_FAILED
    global TREASURE_TAKEN, EVER_DETECTED
    global Door_open, Door_angle
    global Door_blue_open, Door_purple_open, Door_cyan_open, Door_green_open
    global Door_blue_angle, Door_purple_angle, Door_cyan_angle, Door_green_angle
    Door_blue_open = Door_purple_open = Door_cyan_open = Door_green_open = False
    Door_blue_angle = Door_purple_angle = Door_cyan_angle = Door_green_angle = 0.0
    thief_x = 0
    thief_z = -35
    thief_dir_angle = 0.0
    thief_leg_anim = 0.0
    is_hidden = False
    hidden_spot_index = -1
    ALERTED = False
    ALERT_SOURCE = ""
    last_seen_time = -9999.0
    guard_symbol_timer = 0.0
    cctv_symbol_timer = 0.0
    player_spotted_timer = 0.0
    alert_symbol_timer = 0.0
    high_alert_timer = 0.0
    GAME_OVER = False
    MISSION_SUCCESS = False
    MISSION_FAILED = False
    TREASURE_TAKEN = False
    EVER_DETECTED = False
    Door_open = False
    Door_angle = 0.0
    init_guard()
    init_power_button()
    clear_movement_inputs()
    glutPostRedisplay()


def init_power_button():
    global POWER_BUTTON_X, POWER_BUTTON_Z
    oven_x = Floor_width - 2.2
    oven_z = 11.0
    wall_inner_x = Floor_width
    POWER_BUTTON_X = wall_inner_x - 0.12
    POWER_BUTTON_Z = oven_z


def Main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(1400, 900)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Robbery Lou: Treasure Heist")
    glEnable(GL_DEPTH_TEST)
    clearColor = (0.5, 0.8, 1.0, 1.0)
    glClearColor(*clearColor)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 1400 / 900, 0.1, 1000)
    PlaceTrees()
    init_hide_spots()
    init_guard()
    init_power_button()
    glutIdleFunc(Animate)
    glutDisplayFunc(Display_Scene)
    glutKeyboardFunc(handle_keys)
    glutKeyboardUpFunc(handle_keys_up)
    glutSpecialFunc(ArrowKeyControl)
    glutSpecialUpFunc(ArrowKeyUp)
    glutMainLoop()


if __name__ == "__main__":
    Main()