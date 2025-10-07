import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'slot_selection_page.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';

class BookSlotPage extends StatefulWidget {
  const BookSlotPage({super.key});

  @override
  State<BookSlotPage> createState() => _BookSlotPageState();
}

class _BookSlotPageState extends State<BookSlotPage> {
  List<dynamic> _stations = [];
  Map<String, List<dynamic>> _slotsMap = {};
  Map<String, double> _ratingsMap = {};
  bool _isLoading = true;
  String _errorMessage = '';
  String _currentCity = 'Detecting location...';
  bool _isCityLoading = true;
  bool _showStations = false;

  @override
  void initState() {
    super.initState();
    _fetchStations();
    _getCurrentCity();
  }

  Future<void> _fetchStations() async {
    // Backend base URL - update this if needed
    const String backendBaseUrl = 'http://localhost:8000';

    final url = '$backendBaseUrl/parking-spots';

    print('Fetching stations from $url'); // Debug log

    try {
      final response = await http.get(Uri.parse(url));
      print('Response status: ${response.statusCode}'); // Debug log
      print('Raw response body: ${response.body}'); // Detailed raw response log
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('Response data: $data'); // Debug log

        // Fetch slots and reviews for each station
        for (var station in data) {
          final stationId = station['_id'];
          if (stationId == null) {
            continue; // Skip stations with null id
          }
          // Fetch slots
          final slotsResponse =
              await http.get(Uri.parse('$backendBaseUrl/slots/$stationId'));
          List<dynamic> slots = [];
          if (slotsResponse.statusCode == 200) {
            slots = json.decode(slotsResponse.body);
          }
          // Fetch reviews
          final reviewsResponse =
              await http.get(Uri.parse('$backendBaseUrl/reviews/$stationId'));
          double rating = 0.0;
          if (reviewsResponse.statusCode == 200) {
            final reviewsData = json.decode(reviewsResponse.body);
            rating = reviewsData['average_rating'] != null
                ? (reviewsData['average_rating'] as num).toDouble()
                : 0.0;
          }
          _slotsMap[stationId] = slots;
          _ratingsMap[stationId] = rating;
        }

        setState(() {
          _stations = data;
          _isLoading = false;
          _errorMessage = '';
        });
      } else {
        setState(() {
          _errorMessage =
              'Failed to load stations: HTTP ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      print('Exception caught: $e'); // Debug log
      setState(() {
        _errorMessage = 'Error fetching stations: $e';
        _isLoading = false;
      });
    }
  }

  String _calculateHourlyRate(String stationId) {
    if (_slotsMap.containsKey(stationId)) {
      // For simplicity, take the minimum price among slots as hourly rate
      final slots = _slotsMap[stationId]!;
      if (slots.isNotEmpty) {
        double minPrice = double.infinity;
        for (var slot in slots) {
          if (slot['price'] != null) {
            double price = 0.0;
            try {
              price = double.parse(slot['price'].toString());
            } catch (e) {
              price = 0.0;
            }
            if (price < minPrice) {
              minPrice = price;
            }
          }
        }
        if (minPrice != double.infinity) {
          return '\$${minPrice.toStringAsFixed(2)} / hr';
        }
      }
    }
    return '-';
  }

  Future<void> _getCurrentCity() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        throw Exception('Location services are disabled.');
      }
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          throw Exception('Location permissions are denied');
        }
      }
      if (permission == LocationPermission.deniedForever) {
        throw Exception('Location permissions are permanently denied');
      }
      Position position = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.high);
      List<Placemark> placemarks =
          await placemarkFromCoordinates(position.latitude, position.longitude);
      String city = placemarks.first.locality ?? 'Unknown';
      if (city.toLowerCase().contains('bangalore')) {
        city = 'Bangalore';
      }
      setState(() {
        _currentCity = city;
        _isCityLoading = false;
        _showStations = true;
      });
    } catch (e) {
      setState(() {
        _currentCity = 'No location found';
        _isCityLoading = false;
        _showStations = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    print(
        'Building BookSlotPage with ${_stations.length} stations'); // Debug print
    return Scaffold(
      appBar: AppBar(
        title: const Text('Book Slot'),
        backgroundColor: const Color(0xFF2979FF),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Text(
              _isCityLoading
                  ? 'Detecting location...'
                  : 'Current City: $_currentCity',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: TextField(
              decoration: const InputDecoration(
                hintText: 'Search parking stations...',
                border: OutlineInputBorder(),
              ),
              // onChanged: (value) {}, // non-functional
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _errorMessage.isNotEmpty
                    ? Center(child: Text(_errorMessage))
                    : !_showStations
                        ? const Center(
                            child: Text(
                                'Location not detected. Cannot display stations.'))
                        : _stations.isEmpty
                            ? const Center(
                                child: Text(
                                  'No parking stations available.',
                                  style: TextStyle(
                                      color: Colors.white, fontSize: 16),
                                ),
                              )
                            : ListView.builder(
                                itemCount: _stations.length,
                                itemBuilder: (context, index) {
                                  final station = _stations[index];
                                  return Card(
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    elevation: 3,
                                    margin: const EdgeInsets.symmetric(
                                        vertical: 8, horizontal: 16),
                                    child: Padding(
                                      padding: const EdgeInsets.all(16.0),
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Row(
                                            mainAxisAlignment:
                                                MainAxisAlignment.spaceBetween,
                                            children: [
                                              Expanded(
                                                child: Text(
                                                  station['stationName'] ??
                                                      station['name'] ??
                                                      'Unknown',
                                                  style: const TextStyle(
                                                      fontSize: 18,
                                                      fontWeight:
                                                          FontWeight.bold),
                                                ),
                                              ),
                                              Container(
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                        horizontal: 8,
                                                        vertical: 4),
                                                decoration: BoxDecoration(
                                                  color: Colors.green[100],
                                                  borderRadius:
                                                      BorderRadius.circular(20),
                                                ),
                                                child: const Text(
                                                  'OPEN NOW',
                                                  style: TextStyle(
                                                      color: Colors.green,
                                                      fontWeight:
                                                          FontWeight.bold),
                                                ),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 4),
                                          Text(
                                            station['address'] ?? '',
                                            style: const TextStyle(
                                                color: Colors.grey,
                                                fontSize: 14),
                                          ),
                                          const SizedBox(height: 12),
                                          Row(
                                            mainAxisAlignment:
                                                MainAxisAlignment.spaceBetween,
                                            children: [
                                              Row(
                                                children: [
                                                  const Icon(Icons.attach_money,
                                                      color: Colors.orange),
                                                  const SizedBox(width: 4),
                                                  Text(
                                                    station['_id'] != null
                                                        ? _calculateHourlyRate(
                                                            station['_id'])
                                                        : '-',
                                                    style: const TextStyle(
                                                        fontWeight:
                                                            FontWeight.bold),
                                                  ),
                                                ],
                                              ),
                                              Row(
                                                children: [
                                                  const Icon(Icons.star,
                                                      color: Colors.amber),
                                                  const SizedBox(width: 4),
                                                  Text(
                                                    station['_id'] != null &&
                                                            _ratingsMap[station[
                                                                    '_id']] !=
                                                                null
                                                        ? '${_ratingsMap[station['_id']]!.toStringAsFixed(1)}/5'
                                                        : 'N/A',
                                                    style: const TextStyle(
                                                        fontWeight:
                                                            FontWeight.bold),
                                                  ),
                                                ],
                                              ),
                                              Row(
                                                children: [
                                                  const Icon(Icons.location_on,
                                                      color: Colors.brown),
                                                  const SizedBox(width: 4),
                                                  Text(
                                                    '${station['distance']?.toStringAsFixed(1) ?? '-'} miles',
                                                    style: const TextStyle(
                                                        fontWeight:
                                                            FontWeight.bold),
                                                  ),
                                                ],
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 12),
                                          Row(
                                            children: [
                                              if (station['Security'] != null ||
                                                  station['security'] != null)
                                                Row(
                                                  children: const [
                                                    Text('🔒 Security'),
                                                    SizedBox(width: 8),
                                                  ],
                                                ),
                                              if (station['EV Charging'] !=
                                                      null ||
                                                  station['ev_charging'] !=
                                                      null)
                                                Row(
                                                  children: const [
                                                    Text('⚡ EV Charging'),
                                                    SizedBox(width: 8),
                                                  ],
                                                ),
                                              if (station['Accessible'] !=
                                                      null ||
                                                  station['accessible'] != null)
                                                Row(
                                                  children: const [
                                                    Text('♿ Accessible'),
                                                    SizedBox(width: 8),
                                                  ],
                                                ),
                                            ],
                                          ),
                                          const SizedBox(height: 12),
                                          Align(
                                            alignment: Alignment.centerRight,
                                            child: ElevatedButton(
                                              onPressed: () {
                                                Navigator.push(
                                                  context,
                                                  MaterialPageRoute(
                                                    builder: (context) =>
                                                        SlotSelectionPage(
                                                            station: station),
                                                  ),
                                                );
                                              },
                                              child: const Text('Book'),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  );
                                },
                              ),
          ),
        ],
      ),
    );
  }
}
