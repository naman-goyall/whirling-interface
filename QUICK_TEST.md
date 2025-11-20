# Quick Testing Guide - Orbit Gesture System

## Prerequisites
1. Ensure you have a working webcam
2. Virtual environment activated
3. All dependencies installed

## Test Run

```bash
# Navigate to project directory
cd /Users/namangoyal/Desktop/CV_hand_gesture

# Activate virtual environment
source venv/bin/activate

# Run the orbit controller
python tv_orbit_controller.py
```

## What to Expect

### When You Start
1. Camera feed opens
2. Black screen (no video channels loaded yet - that's OK)
3. Message: "Show your hand to see orbit gestures"

### When Hand Detected
1. Top bar appears showing:
   - Title: "TV Orbit Controller (Whirling Style)"
   - Status: Channel, Volume, Play State
2. Right side shows 6 orbit displays (3×2 grid)
3. Each orbit has:
   - Gray circle (path)
   - Yellow ball (moving position)
   - White arrow (direction)
   - Label with command name

### Testing Each Gesture

#### 1. Channel Up (Slow Clockwise)
- **Speed**: Very slow, ~3 seconds per circle
- **Direction**: Clockwise (like stirring)
- **What to watch**: Top-left orbit display
- **Expected**: Correlation score increases, box changes color

#### 2. Channel Down (Slow Counter-Clockwise)
- **Speed**: Very slow, ~3 seconds per circle
- **Direction**: Counter-clockwise (reverse stirring)
- **What to watch**: Top-right orbit display

#### 3. Volume Up (Fast Clockwise)
- **Speed**: Fast, ~1.5 seconds per circle
- **Direction**: Clockwise
- **What to watch**: Middle-left orbit display
- **Expected**: Green feedback when detected, "Volume: XX%" shown

#### 4. Volume Down (Fast Counter-Clockwise)
- **Speed**: Fast, ~1.5 seconds per circle
- **Direction**: Counter-clockwise
- **What to watch**: Middle-right orbit display

#### 5. Play (Medium Clockwise)
- **Speed**: Medium, ~2 seconds per circle
- **Direction**: Clockwise
- **What to watch**: Bottom-left orbit display

#### 6. Pause (Medium Counter-Clockwise)
- **Speed**: Medium, ~2 seconds per circle
- **Direction**: Counter-clockwise
- **What to watch**: Bottom-right orbit display

## Step-by-Step Test Procedure

### Test 1: Volume Control (Easiest)
```
1. Show hand to camera
2. Start moving in FAST circles (1.5 sec per rotation)
3. Go CLOCKWISE
4. Watch middle-left box:
   - Gray → Dark Cyan → Yellow (0.75+) → Green (0.85+)
5. Keep going for 1.5 more seconds
6. Box turns RED briefly
7. Command executes: "Volume: 55%" (increases by 5)
```

### Test 2: Speed Differentiation
```
1. Try FAST clockwise (Volume Up)
   - ~1.5 sec per rotation
   - Should trigger middle-left box
   
2. Now try SLOW clockwise (Channel Up)
   - ~3 sec per rotation
   - Should trigger top-left box instead
   
3. Verify they detect different commands!
```

### Test 3: Direction Differentiation
```
1. Try FAST clockwise (Volume Up)
   - Middle-left box responds
   
2. Try FAST counter-clockwise (Volume Down)
   - Middle-right box responds
   
3. Verify opposite directions trigger different commands!
```

## Color Code Reference

| Color | State | Meaning |
|-------|-------|---------|
| Dark Gray (40,40,40) | Low correlation | Not matching |
| Dark Cyan (100,100,0) | Medium (0.5-0.7) | Somewhat matching |
| Light Yellow (0,200,200) | High (>0.7) | Matching well |
| Yellow (0,255,255) | PERFORMING | Above 0.75 threshold |
| Green (0,255,0) | PENDING | Above 0.85, keep going! |
| Red (0,0,255) | SELECTED | Command executed! |

## Troubleshooting

### Hand Not Detected
- Check lighting
- Make sure hand is visible to camera
- Try moving closer/farther

### Low Correlation (< 0.5)
- **If all orbits low**: Move hand in more circular motion
- **If wrong orbit high**: Adjust your speed
  - Too fast → Go slower
  - Too slow → Go faster

### Gesture Not Triggering
- Check if correlation reaches 0.85 (green box)
- Hold the pattern for full 1.5 seconds
- Make smoother, more consistent circles

### Wrong Command Triggering
- **Channel when expecting Volume**: Speed up your circles
- **Volume when expecting Channel**: Slow down your circles
- **Opposite command**: Check your direction (CW vs CCW)

## Expected Behavior

### Successful Detection Flow
```
1. Start circular motion
   → Correlation starts rising
   
2. Match speed/direction
   → One box shows higher correlation than others
   → Correlation > 0.5: Box color changes
   
3. Good match
   → Correlation > 0.75: Box turns YELLOW (PERFORMING)
   
4. Excellent match
   → Correlation > 0.85: Box turns GREEN (PENDING)
   
5. Hold for 1.5 seconds
   → Box turns RED (SELECTED)
   → Command text appears at top
   → System returns to IDLE
```

### Typical Correlation Scores
- **Random motion**: 0.0 - 0.3
- **Circular but wrong speed**: 0.3 - 0.6
- **Right speed, wrong direction**: 0.4 - 0.7
- **Good match**: 0.7 - 0.85
- **Excellent match**: 0.85 - 1.0

## Performance Tips

### For Best Results
1. **Smooth circles**: Avoid jerky motions
2. **Consistent radius**: Keep circle size similar throughout
3. **Watch the reference**: Match your timing to the orbiting ball
4. **Practice speed differences**: 
   - Slow (3s) vs Medium (2s) vs Fast (1.5s)
5. **Full rotations**: Complete at least 2-3 full circles

### Common Mistakes
- ❌ Moving too fast for all gestures
- ❌ Stopping mid-circle
- ❌ Making ovals instead of circles
- ❌ Varying speed during gesture
- ✅ Smooth, consistent circular motion at target speed

## Debug Mode

### Check Console Output
The program prints useful debug info:
```
Command: Volume: 55%
Command: Channel: 2
Command: Playing
```

### Keyboard Commands
- `q`: Quit program
- `r`: Reset gesture detection (clears history)

## Next Steps After Testing

If orbit detection works well:
1. Test with actual video channels in `/channels` folder
2. Integrate with real TV control (if applicable)
3. Adjust parameters in `orbit_gesture_recognizer.py`:
   - Thresholds (LOW_THRESHOLD, HIGH_THRESHOLD)
   - Time requirements (PENDING_TIME_THRESHOLD)
   - Speed values (period parameters)

## Comparison Test

Try both systems to see the difference:

```bash
# New orbit system (position-independent)
python tv_orbit_controller.py

# Original shape system (needs cursor following)
python tv_gesture_controller.py
```

**Key Differences:**
- Orbit: Perform anywhere, match speed/direction
- Shape: Follow cursor, trace specific shapes
