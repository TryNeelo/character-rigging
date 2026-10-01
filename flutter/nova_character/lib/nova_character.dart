/// Nova, Neelo's talking character, ready to drop into a screen.
///
/// ```dart
/// final nova = NovaController();
///
/// NovaCharacter(controller: nova, framing: NovaFraming.waistUp, align: NovaAlign.right, outfit: 'aviator');
///
/// nova.events.listen((e) => print(e.name));
/// await nova.play('onboarding_nova_dialogue1');
/// ```
library;

export 'src/controller.dart' show NovaController, NovaEvent, NovaLook;
export 'src/line.dart' show NovaLine, NovaCue, NovaMarker;
export 'src/nova_character.dart' show NovaCharacter, NovaFraming, NovaAlign;
