import 'package:flutter/material.dart';
import 'fastag_recharge_page.dart';
import 'buynewfastag_page.dart';
import 'transactionhistory_page.dart';
import 'linkvehiclepage_page.dart';
import 'deactivatefastag_page.dart';

class FastagPage extends StatefulWidget {
  const FastagPage({super.key});

  @override
  State<FastagPage> createState() => _FastagPageState();
}

class _FastagPageState extends State<FastagPage> {
  final Color darkGray = const Color(0xFF1E1E1E);
  final Color electricBlue = const Color(0xFF2979FF);

  double balance = 520.75;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: darkGray,
      appBar: AppBar(
        title: const Text("FASTag"),
        backgroundColor: darkGray,
        elevation: 0,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Balance Card with Recharge Button
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: electricBlue,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "FASTag Balance",
                    style: TextStyle(color: Colors.white70, fontSize: 16),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "₹ ${balance.toStringAsFixed(2)}",
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Recharge button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () async {
                        final result = await Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const FastagRechargePage(),
                          ),
                        );
                        if (result != null && result is double) {
                          setState(() {
                            balance += result;
                          });
                        }
                      },
                      icon: const Icon(Icons.add_circle_outline),
                      label: const Text("Recharge"),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: electricBlue,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // FASTag Services Section
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "FASTag Services",
                style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.white),
              ),
            ),
            const SizedBox(height: 12),

            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 3 / 2,
                children: [
                  ServiceCard(
                    icon: Icons.add_box,
                    title: "Buy New FASTag",
                    electricBlue: electricBlue,
                    darkGray: darkGray,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => BuyNewFastagPage()),
                      );
                    },
                  ),
                  ServiceCard(
                    icon: Icons.history,
                    title: "Transaction History",
                    electricBlue: electricBlue,
                    darkGray: darkGray,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const TransactionHistoryPage()),
                      );
                    },
                  ),
                  ServiceCard(
                    icon: Icons.link,
                    title: "Link Vehicle",
                    electricBlue: electricBlue,
                    darkGray: darkGray,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const LinkVehiclePage()),
                      );
                    },
                  ),
                  ServiceCard(
                    icon: Icons.cancel,
                    title: "Deactivate FASTag",
                    electricBlue: electricBlue,
                    darkGray: darkGray,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const DeactivateFastagPage()),
                      );
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Service Card Widget
class ServiceCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;
  final Color electricBlue;
  final Color darkGray;

  const ServiceCard({
    super.key,
    required this.icon,
    required this.title,
    required this.onTap,
    required this.electricBlue,
    required this.darkGray,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Card(
        color: darkGray,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        elevation: 3,
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 40, color: electricBlue),
              const SizedBox(height: 8),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                    fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
