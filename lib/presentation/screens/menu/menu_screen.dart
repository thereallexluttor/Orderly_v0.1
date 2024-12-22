import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'constants/menu_constants.dart';
import 'controllers/menu_screen_controller.dart';
import 'widgets/category_card.dart';
import 'widgets/menu_header.dart';
import 'components/category_items_content.dart';
import 'components/menu_form.dart';

class MenuScreen extends StatefulWidget {
  const MenuScreen({super.key});

  @override
  State<MenuScreen> createState() => _MenuScreenState();
}

class _MenuScreenState extends State<MenuScreen> {
  final ScrollController _scrollController = ScrollController();
  late MenuScreenController _controller;

  @override
  void initState() {
    super.initState();
    _controller = MenuScreenController();
    _controller.loadCategories();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider.value(
      value: _controller,
      child: Scaffold(
        backgroundColor: Colors.white,
        body: RefreshIndicator(
          onRefresh: _controller.loadCategories,
          child: _buildContent(),
        ),
      ),
    );
  }

  Widget _buildContent() {
    return Container(
      padding: const EdgeInsets.all(MenuConstants.padding),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const MenuHeader(),
          const SizedBox(height: 24),
          Expanded(
            child: Consumer<MenuScreenController>(
              builder: (context, controller, _) {
                if (controller.showForm) {
                  return MenuForm(
                    onClose: controller.toggleForm,
                  );
                }
                return _buildCategoriesGrid(controller);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoriesGrid(MenuScreenController controller) {
    return CustomScrollView(
      controller: _scrollController,
      slivers: [
        const SliverToBoxAdapter(
          child: Padding(
            padding: MenuConstants.categoryPadding,
            child: Text(
              'Categorías',
              style: TextStyle(
                fontSize: MenuConstants.categoryTitleSize,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        SliverGrid(
          delegate: SliverChildBuilderDelegate(
            (context, index) => CategoryCard(
              category: controller.categories[index],
              onTap: () => controller.selectCategory(
                controller.categories[index]['food_category'],
              ),
            ),
            childCount: controller.categories.length,
          ),
          gridDelegate: MenuConstants.gridDelegate,
        ),
        if (controller.selectedCategory != null)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.only(top: 24),
              child: SizedBox(
                height: 900,
                child: CategoryItemsContent(
                  category: controller.selectedCategory!,
                  onClose: () => controller.selectCategory(null),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
