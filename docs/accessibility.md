# JustAsk Mobile App - Accessibility Testing Guide

**Phase 3: Section 3.4 - Accessibility Testing**

Test execution: Manual with accessibility tools
Expected duration: 20-30 minutes
Test date: ____________________
Tested by: ____________________

---

## Pre-Test Setup

### Environment
- [ ] Android device or emulator running (Android 8.0+)
- [ ] App installed and running
- [ ] Network connection available

### Accessibility Tools
- [ ] TalkBack enabled (Android screen reader)
- [ ] Magnification enabled (optional)
- [ ] Font size settings available
- [ ] Color contrast analyzer (optional)

### Enable TalkBack (Screen Reader)
1. Settings → Accessibility → TalkBack
2. Toggle ON
3. App will read all UI elements aloud

---

## Accessibility Test 1: Screen Reader Compatibility (TalkBack)

**Objective**: All UI elements readable by screen reader

### Test 1a: HomeScreen Navigation
**Steps**
1. Enable TalkBack
2. Open app
3. Navigate using TalkBack gestures:
   - Swipe right: Next element
   - Swipe left: Previous element
   - Double tap: Activate
4. Navigate through all elements:
   - Input field
   - Send button
   - Response area
   - Error messages
   - Settings tab

### Expected Results
- [ ] Input field announced: "Ask me something, text input"
- [ ] Send button announced: "Send button"
- [ ] Response area announced with content
- [ ] Settings tab announced
- [ ] All buttons and inputs have labels
- [ ] Screen reader doesn't crash
- [ ] Navigation is logical (top to bottom, left to right)

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 1b: Response Readability
**Steps**
1. Send query (with TalkBack enabled)
2. Wait for response
3. TalkBack should announce response content
4. Verify full response is read (not truncated)

### Expected Results
- [ ] Response text fully readable via TalkBack
- [ ] No critical information missing
- [ ] Response time announced
- [ ] Model name announced
- [ ] Category announced
- [ ] Badges (Cached, Queued) announced

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

### Test 1c: Error Messages
**Steps**
1. Trigger errors:
   - Send empty query
   - Go offline and send query
   - Timeout error
2. Verify TalkBack announces error

### Expected Results
- [ ] Error messages announced clearly
- [ ] Error type understandable
- [ ] Recovery action clear
- [ ] Not just visual (red color)

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 2: Content Descriptions (Voice Labels)

**Objective**: All buttons and icons have meaningful descriptions

### Test 2a: Send Button
**Steps**
1. With TalkBack on
2. Focus on Send button
3. Verify announcement

### Expected Results
- [ ] Announced as: "Send button" or "Send query"
- [ ] Not just: "Button" or "Icon"
- [ ] Describes action (not just appearance)

### Status
- **Pass** ✅ / **Fail** ❌

### Test 2b: Offline Banner Icon
**Steps**
1. Go offline (airplane mode)
2. Focus on cloud icon in offline banner
3. Verify TalkBack announcement

### Expected Results
- [ ] Announced: "Offline" or "No internet connection"
- [ ] Icon purpose clear
- [ ] Not silent/no announcement

### Status
- **Pass** ✅ / **Fail** ❌

### Test 2c: Settings Tab
**Steps**
1. Focus on Settings tab
2. Verify announcement

### Expected Results
- [ ] Announced: "Settings tab" or "Settings"
- [ ] Purpose clear
- [ ] Not just: "Tab"

### Status
- **Pass** ✅ / **Fail** ❌

### Test 2d: Response Badges
**Steps**
1. Cache a response (send same query twice)
2. Focus on "Cached response" badge
3. Verify announcement

### Expected Results
- [ ] Announced: "Cached response" badge
- [ ] Icon described (layers icon = cached)
- [ ] User understands badge purpose

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 3: Text Size & Readability

**Objective**: Text remains readable at various sizes

### Test 3a: Default Text Size
**Steps**
1. Disable TalkBack
2. View app with default system text size
3. Check readability

### Expected Results
- [ ] All text readable (minimum 14sp/14pt)
- [ ] No truncation or clipping
- [ ] Sufficient contrast
- [ ] Good line spacing

### Status
- **Pass** ✅ / **Fail** ❌

### Test 3b: Large Text Size
**Steps**
1. Settings → Display → Font size
2. Set to **Large** or **Extra Large**
3. Open app
4. Check layout and readability

### Expected Results
- [ ] Text enlarges properly
- [ ] Layout adjusts (wraps text if needed)
- [ ] No overlap of elements
- [ ] Buttons still tappable (44x44pt minimum)
- [ ] Input field expands appropriately
- [ ] Response area scrollable if needed

### Status
- **Pass** ✅ / **Fail** ❌

### Test 3c: Bold Text
**Steps**
1. Settings → Display → Font → Bold
2. Reopen app
3. Check appearance

### Expected Results
- [ ] Text displays in bold
- [ ] Readability improved
- [ ] Layout not broken
- [ ] Labels remain clear

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 4: Color Contrast

**Objective**: Text has sufficient contrast for low vision users

### Test 4a: Visual Inspection
**Steps**
1. Review colors:
   - Input text: Dark on light
   - Error text: Red on white/light
   - Labels: Dark on light
   - Info bar: Dark on light
2. Compare contrast ratios

### Expected Results
- [ ] Text color contrast ratio ≥ 4.5:1 (normal text)
- [ ] Large text contrast ratio ≥ 3:1
- [ ] Error messages in red + text (not color alone)
- [ ] No light gray text on white
- [ ] No dark gray text on black

### Status
- **Pass** ✅ / **Fail** ❌

### Test 4b: Color Blindness Mode
**Steps**
1. Enable Color Correction: Settings → Accessibility → Color Correction
2. Test Deuteranopia (red-green blindness)
3. Verify error messages still visible

### Expected Results
- [ ] Error messages visible in color blindness mode
- [ ] Not relying on red alone
- [ ] Text/icon patterns help distinguish
- [ ] Offline banner understandable

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 5: Touch Target Size

**Objective**: All buttons and inputs are easily tappable

### Test 5a: Minimum Touch Target Size
**Steps**
1. Review all tappable elements:
   - Send button
   - Settings tab
   - Input field
   - Response area
2. Measure (target: 44x44 dp/pixels minimum)

### Expected Results
- [ ] Send button: 40x40 dp (minimum acceptable)
- [ ] Input field: ≥ 44 dp tall
- [ ] Settings tab: ≥ 44 dp tall
- [ ] No tiny buttons
- [ ] Sufficient padding around buttons

### Status
- **Pass** ✅ / **Fail** ❌

### Test 5b: Touch Accuracy
**Steps**
1. Attempt to tap each button
2. Try tapping with eyes closed (with TalkBack)
3. Verify easy activation

### Expected Results
- [ ] No accidental button presses
- [ ] Adequate spacing between elements
- [ ] Easy to hit intended target
- [ ] Feedback on successful tap

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 6: Keyboard Navigation

**Objective**: App fully navigable via keyboard (for future BT keyboards/accessibility)

### Test 6a: Tab Order
**Steps**
1. Connect Bluetooth keyboard
2. Use Tab key to navigate through elements
3. Verify tab order is logical

### Expected Results
- [ ] Tab moves through: Input → Send Button → Response → Settings
- [ ] Tab order is sequential (not random)
- [ ] No hidden elements skipped
- [ ] Reverse tab (Shift+Tab) works

### Status
- **Pass** ✅ / **Fail** ❌ / **N/A** (No BT keyboard)

### Test 6b: Enter/Activate
**Steps**
1. Tab to Send button
2. Press Enter
3. Verify button activates

### Expected Results
- [ ] Enter activates Send button
- [ ] Query sends
- [ ] No keyboard-specific bugs

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 7: Focus Indicators

**Objective**: Users know which element is focused

### Test 7a: Visual Focus
**Steps**
1. With TalkBack on, navigate through elements
2. Observe focus indicator (visual border/highlight)

### Expected Results
- [ ] Focused element has clear indicator (border, highlight)
- [ ] Focus indicator has sufficient contrast
- [ ] Focus indicator visible for all interactive elements
- [ ] Focus is obvious (not subtle)

### Status
- **Pass** ✅ / **Fail** ❌

### Test 7b: Focus Movement
**Steps**
1. Swipe right (next element in TalkBack)
2. Observe focus move smoothly
3. Repeat several times

### Expected Results
- [ ] Focus moves one element at a time
- [ ] No jumps or skips
- [ ] Visual focus follows TalkBack focus
- [ ] No "focus lost" scenarios

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 8: Loading States & Feedback

**Objective**: Users informed of loading/state changes

### Test 8a: Loading Spinner
**Steps**
1. Send query
2. Observe loading spinner
3. With TalkBack: Verify announcement

### Expected Results
- [ ] Loading spinner visible
- [ ] TalkBack announces "Loading" or "Busy"
- [ ] User aware of processing
- [ ] Spinner has meaning (not just visual)

### Status
- **Pass** ✅ / **Fail** ❌

### Test 8b: Offline Transition
**Steps**
1. Go online
2. Then go offline (airplane mode)
3. Observe offline banner

### Expected Results
- [ ] Offline banner appears/announced
- [ ] Color change alone isn't only indicator
- [ ] Text clearly states "No internet"
- [ ] TalkBack announces change

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 9: Haptic Feedback (Vibration)

**Objective**: No reliance on haptic feedback alone

### Test 9a: Vibration Settings
**Steps**
1. Settings → Sound & Vibration → Vibration intensity
2. Turn OFF vibration
3. Use app normally

### Expected Results
- [ ] App works without vibration
- [ ] Feedback isn't vibration-only
- [ ] Visual/audio feedback sufficient
- [ ] No confusion without haptics

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 10: Settings Screen Accessibility

**Objective**: Settings/Info screen fully accessible

### Test 10a: Settings with TalkBack
**Steps**
1. Enable TalkBack
2. Tap Settings tab
3. Navigate all elements
4. Verify announcements

### Expected Results
- [ ] All settings readable
- [ ] App version announced
- [ ] Cache info announced (if shown)
- [ ] Buttons clearly described
- [ ] Privacy statement readable
- [ ] No inaccessible elements

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 11: Animations & Transitions

**Objective**: No motion-triggered issues (vestibular sensitivity)

### Test 11a: Reduce Motion
**Steps**
1. Settings → Accessibility → Accessibility Options → Remove Animations
2. (Or: Developer Options → Animation Scale = 0.5x)
3. Open app
4. Send query
5. Observe animations

### Expected Results
- [ ] Animations are optional (not distracting)
- [ ] App still responsive
- [ ] No animations cause motion sickness
- [ ] Transitions are smooth, not jarring
- [ ] App works with animations disabled

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Accessibility Test 12: Language & Clarity

**Objective**: Text is simple and clear

### Test 12a: Simple Language
**Steps**
1. Review all UI text:
   - Button labels
   - Error messages
   - Descriptions
2. Check for clarity

### Expected Results
- [ ] No unnecessary jargon
- [ ] Instructions are clear
- [ ] Error messages explain problem and solution
- [ ] Language is simple (8th grade reading level or lower, ideally)
- [ ] Abbreviations explained

### Status
- **Pass** ✅ / **Fail** ❌

Notes: _____________________________________________________________________

---

## Summary Results

### Test Execution Summary
- Total Accessibility Tests: 15+
- Passed: ___
- Failed: ___
- Blocked: ___
- Success Rate: ___%

### Critical Accessibility Issues
1. _______________________________________________________________________
2. _______________________________________________________________________

### Compliance Assessment

**WCAG 2.1 Level A:**
- [ ] Perceivable: Text readable, colors have contrast
- [ ] Operable: Keyboard navigable, no keyboard traps
- [ ] Understandable: Clear labels and instructions
- [ ] Robust: Works with assistive technology

**Assistive Technology Compatibility:**
- [ ] TalkBack (Android): **PASS** / **FAIL**
- [ ] Magnification: **PASS** / **FAIL**
- [ ] Color Correction: **PASS** / **FAIL**
- [ ] Large Fonts: **PASS** / **FAIL**

### Recommendations for Improvement
1. _______________________________________________________________________
2. _______________________________________________________________________

### Sign-Off
- Tested by: _________________________ Date: __________
- Accessibility Lead: _________________________ Date: __________

---

## Appendix: Accessibility Standards

**WCAG 2.1** (Web Content Accessibility Guidelines)
- Level A: Basic accessibility
- Level AA: Enhanced accessibility (industry standard)
- Level AAA: Advanced accessibility

**Target for MVP:** WCAG 2.1 Level A minimum

**Key Principles:**
1. **Perceivable**: Information must be perceivable to senses
2. **Operable**: Interface must be operable via any input
3. **Understandable**: Information and operation must be clear
4. **Robust**: Compatible with assistive technology

**Common Accessibility Issues to Avoid:**
- ❌ Color as only indicator
- ❌ Images without alt text
- ❌ Unreadable font sizes
- ❌ Poor contrast
- ❌ Keyboard navigation broken
- ❌ No focus indicators
- ❌ Confusing terminology
- ❌ Auto-playing audio/video
