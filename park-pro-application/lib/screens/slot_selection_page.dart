import 'package:flutter/material.dart';

class SlotSelectionPage extends StatefulWidget {
  final dynamic station;

  const SlotSelectionPage({Key? key, required this.station}) : super(key: key);

  @override
  _SlotSelectionPageState createState() => _SlotSelectionPageState();
}

class _SlotSelectionPageState extends State<SlotSelectionPage> {
  List<String> _slots = [];
  String? _selectedSlot;
  bool _isLoading = true;
  String _errorMessage = '';

  @override
  void initState() {
    super.initState();
    _fetchSlots();
  }

  Future<void> _fetchSlots() async {
    // For demo, generate dummy slots or fetch from backend if API available
    await Future.delayed(Duration(seconds: 1)); // simulate network delay
    setState(() {
      _slots = ['Slot 1', 'Slot 2', 'Slot 3', 'Slot 4'];
      _isLoading = false;
      _errorMessage = '';
    });
  }

  void _confirmBooking() {
    if (_selectedSlot == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please select a slot')),
      );
      return;
    }
    // TODO: Implement booking confirmation logic, e.g., call backend API

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Booking Confirmed'),
        content: Text(
            'You have booked $_selectedSlot at ${widget.station['name'] ?? 'the station'}'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context); // close dialog
              Navigator.pop(context); // go back to previous page
            },
            child: Text('OK'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Select Slot - ${widget.station['name'] ?? 'Station'}'),
        backgroundColor: const Color(0xFF2979FF),
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _errorMessage.isNotEmpty
              ? Center(child: Text(_errorMessage))
              : ListView.builder(
                  itemCount: _slots.length,
                  itemBuilder: (context, index) {
                    final slot = _slots[index];
                    return RadioListTile<String>(
                      title: Text(slot),
                      value: slot,
                      groupValue: _selectedSlot,
                      onChanged: (value) {
                        setState(() {
                          _selectedSlot = value;
                        });
                      },
                    );
                  },
                ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ElevatedButton(
          onPressed: _confirmBooking,
          child: Text('Confirm Booking'),
        ),
      ),
    );
  }
}
