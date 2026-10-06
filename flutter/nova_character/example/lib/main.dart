import 'package:flutter/material.dart';
import 'package:nova_character/nova_character.dart';

void main() => runApp(const MaterialApp(debugShowCheckedModeBanner: false, home: NovaDemo()));

/// A sample screen: Nova in a scene, a Play button and a log of the events he sends.
class NovaDemo extends StatefulWidget {
  const NovaDemo({super.key});

  @override
  State<NovaDemo> createState() => _NovaDemoState();
}

class _NovaDemoState extends State<NovaDemo> {
  final nova = NovaController();
  final log = <String>[];
  NovaFraming framing = NovaFraming.waistUp;
  NovaAlign align = NovaAlign.right;
  bool outline = true, halfSpeed = false, movement = true;
  String outfit = 'hoodie';

  @override
  void initState() {
    super.initState();
    // This is where the app reacts to what Nova says.
    nova.events.listen((e) => setState(() => log.insert(0, '${e.time.toStringAsFixed(2)} s   ${e.name}')));
    nova.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    nova.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // The app draws subtitles in its own style; Nova only says which sentence is current
    final subtitle = ValueListenableBuilder<NovaCaption?>(
      valueListenable: nova.caption,
      builder: (context, caption, _) => AnimatedOpacity(
        opacity: caption == null ? 0 : 1,
        duration: const Duration(milliseconds: 150),
        child: Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
          child: Text(caption?.text ?? '', textAlign: TextAlign.center, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
        ),
      ),
    );
    final scene = Container(
      decoration: BoxDecoration(color: const Color(0xFFC3DEDB), borderRadius: BorderRadius.circular(16)),
      clipBehavior: Clip.antiAlias,
      child: Stack(children: [Positioned.fill(child: NovaCharacter(controller: nova, framing: framing, align: align, outline: outline, outfit: outfit, idle: movement)),
        Positioned(left: 0, right: 0, bottom: 0, child: Center(child: subtitle)),
      ]),
    );
    final controls = ListView(padding: const EdgeInsets.all(16), children: [
      Text('Nova demo', style: Theme.of(context).textTheme.headlineSmall),
      const SizedBox(height: 12),
      Row(children: [
        FilledButton(
          onPressed: () => nova.isSpeaking
              ? nova.stop()
              : nova.play('onboarding_nova_dialogue1', speed: halfSpeed ? 0.5 : 1),
          child: Text(nova.isSpeaking ? 'Stop' : 'Play line'),
        ),
        const SizedBox(width: 12),
        FilterChip(label: const Text('Half speed'), selected: halfSpeed, onSelected: (v) => setState(() => halfSpeed = v)),
      ]),
      const SizedBox(height: 16),
      SegmentedButton<String>(
        segments: const [
          ButtonSegment(value: 'hoodie', label: Text('Hoodie')),
          ButtonSegment(value: 'aviator', label: Text('Aviator')),
          ButtonSegment(value: 'construction', label: Text('Construction')),
        ],
        selected: {outfit},
        onSelectionChanged: (v) => setState(() => outfit = v.first),
      ),
      const SizedBox(height: 12),
      SegmentedButton<NovaFraming>(
        segments: const [
          ButtonSegment(value: NovaFraming.full, label: Text('Full')),
          ButtonSegment(value: NovaFraming.kneesUp, label: Text('Knees')),
          ButtonSegment(value: NovaFraming.waistUp, label: Text('Waist')),
          ButtonSegment(value: NovaFraming.closeUp, label: Text('Close')),
        ],
        selected: {framing},
        onSelectionChanged: (v) => setState(() => framing = v.first),
      ),
      const SizedBox(height: 12),
      SegmentedButton<NovaAlign>(
        segments: const [
          ButtonSegment(value: NovaAlign.left, label: Text('Left')),
          ButtonSegment(value: NovaAlign.center, label: Text('Center')),
          ButtonSegment(value: NovaAlign.right, label: Text('Right')),
        ],
        selected: {align},
        onSelectionChanged: (v) => setState(() => align = v.first),
      ),
      SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: const Text('Movement'),
        subtitle: const Text('Off: Nova only blinks and talks, and stays still in between'),
        value: movement,
        onChanged: (v) => setState(() => movement = v),
      ),
      SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: const Text('White outline'),
        value: outline,
        onChanged: (v) => setState(() => outline = v),
      ),
      const Divider(),
      Text('Events', style: Theme.of(context).textTheme.titleMedium),
      if (log.isEmpty) const Text('Play the line to see events arrive.'),
      for (final l in log) Text(l, style: const TextStyle(fontFamily: 'monospace')),
    ]);

    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(builder: (context, box) {
          final wide = box.maxWidth > 700;
          return wide
              ? Row(children: [
                  Expanded(flex: 3, child: Padding(padding: const EdgeInsets.all(16), child: scene)),
                  Expanded(flex: 2, child: controls),
                ])
              : Column(children: [
                  Expanded(child: Padding(padding: const EdgeInsets.all(16), child: scene)),
                  SizedBox(height: 360, child: controls),
                ]);
        }),
      ),
    );
  }
}
