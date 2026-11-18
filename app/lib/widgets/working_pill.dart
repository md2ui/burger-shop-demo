// The pill shown while the agent works or the home page is freshened, as the web app's:
// a forest pill with three mustard dots bouncing one after another, and what is happening.

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../palette.dart';

class WorkingPill extends StatefulWidget {
  const WorkingPill({super.key, required this.label});
  final String label;

  @override
  State<WorkingPill> createState() => _WorkingPillState();
}

class _WorkingPillState extends State<WorkingPill> with SingleTickerProviderStateMixin {
  late final AnimationController _beat = AnimationController(vsync: this, duration: const Duration(milliseconds: 1000))
    ..repeat();

  @override
  void dispose() {
    _beat.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final still = MediaQuery.of(context).disableAnimations;
    return Semantics(
      liveRegion: true,
      label: widget.label,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: Palette.forest,
          borderRadius: BorderRadius.circular(999),
          boxShadow: [BoxShadow(color: Palette.forest.withValues(alpha: 0.2), blurRadius: 24, offset: const Offset(0, 8))],
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (var i = 0; i < 3; i++)
                Padding(
                  padding: EdgeInsets.only(right: i == 2 ? 10 : 6),
                  child: AnimatedBuilder(
                    animation: _beat,
                    builder: (context, child) {
                      // Each dot rises 4 px and brightens in turn, 0.15 of a beat apart.
                      final t = still ? 0.0 : math.sin(((_beat.value - i * 0.15) % 1.0) * math.pi);
                      return Transform.translate(
                        offset: Offset(0, -4 * t),
                        child: Opacity(opacity: 0.6 + 0.4 * t, child: child),
                      );
                    },
                    child: const SizedBox.square(
                      dimension: 6,
                      child: DecoratedBox(decoration: BoxDecoration(color: Palette.mustard, shape: BoxShape.circle)),
                    ),
                  ),
                ),
              Text(
                widget.label,
                style: const TextStyle(
                  fontFamily: Fonts.heading,
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                  color: Palette.white,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
