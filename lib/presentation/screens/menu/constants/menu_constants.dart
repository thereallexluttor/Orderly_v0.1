import 'package:flutter/material.dart';

class MenuConstants {
  static const double padding = 32.0;
  static const double headerFontSize = 13.8;
  static const double categoryTitleSize = 15.3;
  static const double categoryItemSize = 12.2;

  static const EdgeInsets cardPadding = EdgeInsets.all(15.0);
  static const EdgeInsets categoryPadding = EdgeInsets.only(bottom: 16);

  static const SliverGridDelegateWithMaxCrossAxisExtent gridDelegate =
      SliverGridDelegateWithMaxCrossAxisExtent(
    maxCrossAxisExtent: 250,
    childAspectRatio: 1.2,
    crossAxisSpacing: 16,
    mainAxisSpacing: 16,
  );
}
